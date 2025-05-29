from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from .models import Center, Review, ExternalReview, Therapist, CenterImage, ReviewComment, BackupHistory, RestoreHistory
from .forms import ReviewForm, CenterManagementForm, TherapistManagementForm, ReviewCommentForm
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.db.models import Q
from django.core.paginator import Paginator
import json
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import requests
import csv
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView, ListView
from django.contrib import messages
from django.http import Http404
from django.forms import inlineformset_factory
from django.db import transaction
from django.urls import reverse
import os
import gzip
import subprocess
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.core.management import call_command
from io import StringIO
import tempfile

# 유틸리티 함수들
def escape_quotes(text):
    """문자열에서 따옴표를 이스케이프 처리"""
    if text is None:
        return ""
    return str(text).replace('"', '\\"').replace("'", "\\'")

def format_date_for_json(date_obj):
    """날짜 객체를 JSON 형식으로 변환"""
    if hasattr(date_obj, 'isoformat'):
        return date_obj.isoformat()
    return date_obj.strftime('%Y-%m-%d')

def create_pagination_data(page_obj):
    """페이지네이션 데이터 생성"""
    paginator = page_obj.paginator
    return {
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
    }

def serialize_therapist(therapist):
    """상담사 객체 직렬화"""
    return {
        'name': escape_quotes(therapist.name),
        'photo': escape_quotes(therapist.photo.url) if therapist.photo else None,
        'experience': therapist.experience,
        'specialty': escape_quotes(therapist.specialty),
        'description': escape_quotes(therapist.description)
    }

def serialize_review(review, user=None):
    """리뷰 객체 직렬화"""
    # 댓글 직렬화
    comments_data = []
    for comment in review.comments.filter(is_active=True).order_by('created_at'):
        comments_data.append({
            'id': comment.id,
            'content': escape_quotes(comment.content),
            'author': escape_quotes(comment.author.username),
            'created_at': format_date_for_json(comment.created_at),
            'updated_at': format_date_for_json(comment.updated_at) if comment.updated_at != comment.created_at else None,
            'can_edit': user and comment.author == user
        })
    
    return {
        'id': getattr(review, 'id', None),
        'title': escape_quotes(review.title),
        'content': escape_quotes(getattr(review, 'content', '')),
        'author': escape_quotes(review.user.username if hasattr(review, 'user') and review.user else '익명'),
        'rating': getattr(review, 'rating', 5),
        'created_at': format_date_for_json(review.created_at),
        'is_owner': user and hasattr(review, 'user') and review.user == user,
        'comments': comments_data
    }

def serialize_external_review(review):
    """외부 리뷰 객체 직렬화"""
    return {
        'title': escape_quotes(review.title),
        'summary': escape_quotes(review.summary),
        'source': escape_quotes(review.source),
        'url': escape_quotes(review.url),
        'created_at': format_date_for_json(review.created_at)
    }

def serialize_center(center, user=None):
    """센터 객체 직렬화"""
    try:
        lat = float(center.latitude) if isinstance(center.latitude, Decimal) else center.latitude
        lng = float(center.longitude) if isinstance(center.longitude, Decimal) else center.longitude
        
        return {
            'id': center.id,
            'name': escape_quotes(center.name),
            'type': escape_quotes(center.type),
            'lat': lat,
            'lng': lng,
            'address': escape_quotes(center.address),
            'phone': escape_quotes(center.phone),
            'url': escape_quotes(center.url),
            'operating_hours': escape_quotes(center.operating_hours),
            'description': escape_quotes(center.description),
            'images': [escape_quotes(image.image.url) for image in center.images.all()],
            'therapists': [serialize_therapist(t) for t in center.therapists.all()],
            'reviews': [serialize_review(r, user) for r in center.reviews.all().prefetch_related('comments').order_by('-created_at')],
            'external_reviews': [serialize_external_review(r) for r in center.external_reviews.all().order_by('-created_at')],
            'is_authenticated': user.is_authenticated if user else False
        }
    except Exception as e:
        print(f"Error serializing center {center.id}: {str(e)}")
        return None

def validate_review_data(data):
    """리뷰 데이터 검증"""
    title = data.get('title')
    content = data.get('content')
    rating = data.get('rating')
    
    if not title or not content or not rating:
        raise ValueError('제목, 내용, 평점은 필수입니다.')
    
    try:
        rating = int(rating)
        if not (1 <= rating <= 5):
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError('평점은 1에서 5 사이의 숫자여야 합니다.')
    
    return title, content, rating

# 뷰 함수들
def index(request):
    centers = Center.objects.all().prefetch_related(
        'images', 
        'therapists', 
        'reviews__comments', 
        'external_reviews'
    )
    
    center_list = []
    for center in centers:
        serialized = serialize_center(center, request.user)
        if serialized:
            center_list.append(serialized)

    selected_center_id = request.GET.get('center_id')
    
    return render(request, 'centers/index.html', {
        'centers_json': json.dumps(center_list, ensure_ascii=False),
        'selected_center_id_json': json.dumps(selected_center_id) if selected_center_id else 'null',
        'is_authenticated_json': json.dumps(request.user.is_authenticated),
        'naver_client_id': settings.NAVER_CLIENT_ID
    })

def get_reviews(request, center_id):
    center = get_object_or_404(Center, pk=center_id)
    reviews = Review.objects.filter(center=center).order_by('-created_at').prefetch_related('comments')
    
    page_number = request.GET.get('page', 1)
    paginator = Paginator(reviews, 10)
    page_obj = paginator.get_page(page_number)
    
    reviews_data = [serialize_review(review, request.user) for review in page_obj]
    pagination_data = create_pagination_data(page_obj)
    
    return JsonResponse({
        'reviews': reviews_data,
        'pagination': pagination_data
    })

@login_required
def add_review(request, center_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)
    
    center = get_object_or_404(Center, pk=center_id)
    
    try:
        data = json.loads(request.body)
        title, content, rating = validate_review_data(data)
        
        review = Review.objects.create(
            user=request.user,
            center=center,
            title=title,
            content=content,
            rating=rating,
            created_at=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'review': serialize_review(review, request.user)
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def update_review(request, review_id):
    if request.method != 'PATCH':
        return JsonResponse({'error': 'PATCH 요청만 허용됩니다.'}, status=405)
    
    review = get_object_or_404(Review, pk=review_id)
    
    if review.user != request.user:
        return JsonResponse({'error': '리뷰 수정 권한이 없습니다.'}, status=403)
    
    try:
        data = json.loads(request.body)
        title, content, rating = validate_review_data(data)
        
        review.title = title
        review.content = content
        review.rating = rating
        review.save()
        
        return JsonResponse({
            'success': True,
            'review': serialize_review(review, request.user)
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def delete_review(request, review_id):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'DELETE 요청만 허용됩니다.'}, status=405)
    
    review = get_object_or_404(Review, pk=review_id)
    
    if review.user != request.user:
        return JsonResponse({'error': '리뷰 삭제 권한이 없습니다.'}, status=403)
    
    try:
        review.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def search_results(request):
    query = request.GET.get('q', '')
    centers = []
    
    if query:
        centers = Center.objects.filter(
            Q(name__icontains=query) |
            Q(address__icontains=query) |
            Q(phone__icontains=query) |
            Q(description__icontains=query)
        ).distinct()
    
    return render(request, 'centers/search_results.html', {
        'query': query,
        'centers': centers,
    })

def check_auth(request):
    return JsonResponse({'is_authenticated': request.user.is_authenticated})

@csrf_exempt
def geocode_address(request):
    if request.method != 'POST':
        return JsonResponse({'error': '잘못된 요청입니다.'}, status=400)
    
    try:
        data = json.loads(request.body)
        address = data.get('address')
        
        if not address:
            return JsonResponse({'error': '주소가 필요합니다.'}, status=400)
        
        headers = {
            'X-NCP-APIGW-API-KEY-ID': settings.NAVER_CLIENT_ID,
            'X-NCP-APIGW-API-KEY': settings.NAVER_CLIENT_SECRET
        }
        
        response = requests.get(
            f'https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode',
            params={'query': address},
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('addresses'):
                first_result = result['addresses'][0]
                return JsonResponse({
                    'latitude': float(first_result['y']),
                    'longitude': float(first_result['x'])
                })
        
        return JsonResponse({'error': '주소를 찾을 수 없습니다.'}, status=404)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# 기타 뷰들
def center_detail(request, center_id):
    center = Center.objects.get(pk=center_id)
    reviews = Review.objects.filter(center=center).order_by('-date')

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.center = center
            review.date = timezone.now()
            review.save()
            return redirect('center_detail', center_id=center_id)
    else:
        form = ReviewForm()

    center_images = center.images.all()

    return render(request, 'centers/center_detail.html', {
        'center': center,
        'reviews': reviews,
        'form': form,
        'center_images': center_images,
    })

def review_form(request, center_id):
    center = get_object_or_404(Center, pk=center_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.center = center
            review.user = request.user
            review.rating = form.cleaned_data['rating']
            review.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = ReviewForm()
    return render(request, 'centers/review_form.html', {'form': form, 'center': center})

def get_external_reviews(request, center_id):
    center = get_object_or_404(Center, pk=center_id)
    external_reviews = ExternalReview.objects.filter(center=center).order_by('-created_at')
    
    page_number = request.GET.get('page', 1)
    paginator = Paginator(external_reviews, 10)
    page_obj = paginator.get_page(page_number)
    
    reviews_data = [
        {
            'id': review.id,
            'title': review.title,
            'content': review.content,
            'source': review.source,
            'created_at': format_date_for_json(review.created_at)
        }
        for review in page_obj
    ]
    
    return JsonResponse({
        'reviews': reviews_data,
        'pagination': create_pagination_data(page_obj)
    })

def upload_centers(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        decoded_file = csv_file.read().decode('utf-8')
        
        csv_reader = csv.DictReader(
            decoded_file.splitlines(),
            quotechar='"',
            escapechar='\\',
            doublequote=True
        )
        
        for row in csv_reader:
            try:
                geocode_result = geocode_address(row['address'])
                if not geocode_result:
                    continue
                
                description = row['description'].replace("'", "''") if row['description'] else ""
                
                center = Center.objects.create(
                    name=row['name'],
                    address=row['address'],
                    phone=row['phone'],
                    url=row['url'],
                    description=description,
                    latitude=geocode_result['latitude'],
                    longitude=geocode_result['longitude']
                )
                
                if row.get('image_url'):
                    CenterImage.objects.create(
                        center=center,
                        image_url=row['image_url']
                    )
                    
            except Exception as e:
                print(f"Error processing row: {row}")
                print(f"Error details: {str(e)}")
                continue
        
        return redirect('centers:index')
    
    return render(request, 'centers/upload.html')

class CenterManagerRequiredMixin:
    """센터 관리자 권한이 필요한 뷰를 위한 Mixin"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:account_login')
        
        if not hasattr(request.user, 'profile'):
            messages.error(request, '프로필이 설정되지 않았습니다.')
            return redirect('centers:index')
        
        profile = request.user.profile
        if not (profile.is_admin() or profile.is_center_manager()):
            messages.error(request, '센터 관리 권한이 없습니다. 일반 사용자는 이 페이지에 접근할 수 없습니다.')
            return redirect('centers:index')
        
        return super().dispatch(request, *args, **kwargs)

class CenterManagementView(CenterManagerRequiredMixin, UpdateView):
    """센터 정보 관리 뷰"""
    model = Center
    form_class = CenterManagementForm
    template_name = 'centers/center_management.html'
    context_object_name = 'center'
    
    def get_object(self):
        center_id = self.kwargs.get('pk')
        center = get_object_or_404(Center, pk=center_id)
        
        # 권한 확인
        profile = self.request.user.profile
        if not profile.can_manage_center(center):
            raise Http404("해당 센터를 관리할 권한이 없습니다.")
        
        return center
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 상담사 폼셋 추가
        TherapistFormSet = inlineformset_factory(
            Center, Therapist, 
            form=TherapistManagementForm,
            extra=1, can_delete=True
        )
        
        # 이미지 폼셋 추가
        ImageFormSet = inlineformset_factory(
            Center, CenterImage,
            fields=('image',),
            extra=1, can_delete=True
        )
        
        if self.request.POST:
            context['therapist_formset'] = TherapistFormSet(
                self.request.POST, self.request.FILES, instance=self.object
            )
            context['image_formset'] = ImageFormSet(
                self.request.POST, self.request.FILES, instance=self.object
            )
        else:
            context['therapist_formset'] = TherapistFormSet(instance=self.object)
            context['image_formset'] = ImageFormSet(instance=self.object)
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        therapist_formset = context['therapist_formset']
        image_formset = context['image_formset']
        
        with transaction.atomic():
            if form.is_valid() and therapist_formset.is_valid() and image_formset.is_valid():
                self.object = form.save()
                therapist_formset.instance = self.object
                therapist_formset.save()
                image_formset.instance = self.object
                image_formset.save()
                
                messages.success(self.request, '센터 정보가 성공적으로 업데이트되었습니다.')
                return redirect('centers:center_management', pk=self.object.pk)
            else:
                return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse('centers:center_management', kwargs={'pk': self.object.pk})

class CenterListView(CenterManagerRequiredMixin, ListView):
    """센터 관리자가 관리할 수 있는 센터 목록"""
    model = Center
    template_name = 'centers/center_list_management.html'
    context_object_name = 'centers'
    
    def get_queryset(self):
        profile = self.request.user.profile
        if profile.is_admin():
            return Center.objects.all()
        elif profile.is_center_manager():
            return Center.objects.filter(id=profile.managed_center.id)
        return Center.objects.none()

@login_required
def center_management_dashboard(request):
    """센터 관리 대시보드"""
    if not hasattr(request.user, 'profile'):
        messages.error(request, '프로필이 설정되지 않았습니다.')
        return redirect('centers:index')
    
    profile = request.user.profile
    if not (profile.is_admin() or profile.is_center_manager()):
        messages.error(request, '센터 관리 권한이 없습니다. 일반 사용자는 이 페이지에 접근할 수 없습니다.')
        return redirect('centers:index')
    
    # 관리 가능한 센터 목록
    if profile.is_admin():
        centers = Center.objects.all()
    else:
        centers = Center.objects.filter(id=profile.managed_center.id) if profile.managed_center else Center.objects.none()
    
    context = {
        'centers': centers,
        'profile': profile,
    }
    
    return render(request, 'centers/management_dashboard.html', context)

# 리뷰 관리 관련 뷰들
class ReviewManagementView(CenterManagerRequiredMixin, ListView):
    """센터 관리자용 리뷰 관리 페이지"""
    model = Review
    template_name = 'centers/review_management.html'
    context_object_name = 'reviews'
    paginate_by = 10
    
    def get_queryset(self):
        profile = self.request.user.profile
        
        # 관리 가능한 센터의 리뷰만 조회
        if profile.is_admin():
            queryset = Review.objects.all()
        elif profile.is_center_manager() and profile.managed_center:
            queryset = Review.objects.filter(center=profile.managed_center)
        else:
            queryset = Review.objects.none()
        
        # 검색 기능
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(user__username__icontains=search_query)
            )
        
        return queryset.select_related('user', 'center').prefetch_related('comments').order_by('-created_at')
    
    def get_unanswered_reviews(self):
        """답변이 없는 리뷰들을 반환"""
        profile = self.request.user.profile
        
        # 관리 가능한 센터의 리뷰만 조회
        if profile.is_admin():
            queryset = Review.objects.all()
        elif profile.is_center_manager() and profile.managed_center:
            queryset = Review.objects.filter(center=profile.managed_center)
        else:
            queryset = Review.objects.none()
        
        # 검색 기능
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(user__username__icontains=search_query)
            )
        
        # 댓글이 없는 리뷰만 필터링
        unanswered_reviews = queryset.filter(comments__isnull=True).select_related('user', 'center').prefetch_related('comments').order_by('-created_at')
        
        return unanswered_reviews
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['profile'] = self.request.user.profile
        
        # 미응답 리뷰 추가
        context['unanswered_reviews'] = self.get_unanswered_reviews()
        context['unanswered_count'] = context['unanswered_reviews'].count()
        
        return context

@login_required
def add_review_comment(request, review_id):
    """리뷰에 댓글 추가"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)
    
    review = get_object_or_404(Review, pk=review_id)
    
    # 권한 확인
    if not hasattr(request.user, 'profile'):
        return JsonResponse({'error': '프로필이 설정되지 않았습니다.'}, status=403)
    
    profile = request.user.profile
    if not (profile.is_admin() or (profile.is_center_manager() and profile.managed_center == review.center)):
        return JsonResponse({'error': '댓글을 작성할 권한이 없습니다.'}, status=403)
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        if not content:
            return JsonResponse({'error': '댓글 내용을 입력해주세요.'}, status=400)
        
        comment = ReviewComment.objects.create(
            review=review,
            author=request.user,
            content=content
        )
        
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'author': comment.author.username,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
                'can_edit': True
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def update_review_comment(request, comment_id):
    """리뷰 댓글 수정"""
    if request.method != 'PATCH':
        return JsonResponse({'error': 'PATCH 요청만 허용됩니다.'}, status=405)
    
    comment = get_object_or_404(ReviewComment, pk=comment_id)
    
    # 권한 확인 (댓글 작성자만 수정 가능)
    if comment.author != request.user:
        return JsonResponse({'error': '댓글을 수정할 권한이 없습니다.'}, status=403)
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        if not content:
            return JsonResponse({'error': '댓글 내용을 입력해주세요.'}, status=400)
        
        comment.content = content
        comment.save()
        
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'author': comment.author.username,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': comment.updated_at.strftime('%Y-%m-%d %H:%M'),
                'can_edit': True
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def delete_review_comment(request, comment_id):
    """리뷰 댓글 삭제"""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'DELETE 요청만 허용됩니다.'}, status=405)
    
    comment = get_object_or_404(ReviewComment, pk=comment_id)
    
    # 권한 확인 (댓글 작성자만 삭제 가능)
    if comment.author != request.user:
        return JsonResponse({'error': '댓글을 삭제할 권한이 없습니다.'}, status=403)
    
    try:
        comment.delete()
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_review_comments(request, review_id):
    """리뷰의 댓글 목록 조회"""
    review = get_object_or_404(Review, pk=review_id)
    comments = ReviewComment.objects.filter(review=review, is_active=True).order_by('created_at')
    
    comments_data = []
    for comment in comments:
        comments_data.append({
            'id': comment.id,
            'content': comment.content,
            'author': comment.author.username,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': comment.updated_at.strftime('%Y-%m-%d %H:%M') if comment.updated_at != comment.created_at else None,
            'can_edit': comment.author == request.user
        })
    
    return JsonResponse({
        'success': True,
        'comments': comments_data
    })

def is_superuser(user):
    return user.is_superuser

@user_passes_test(is_superuser)
def backup_dashboard(request):
    """백업/복원 대시보드"""
    # GitHub API에서 실제 백업 히스토리 가져오기
    backup_history = []
    try:
        token = getattr(settings, 'GITHUB_TOKEN', None) or os.getenv('GITHUB_TOKEN')
        repo = getattr(settings, 'GITHUB_BACKUP_REPO', None) or os.getenv('GITHUB_BACKUP_REPO')
        
        if token and repo:
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # GitHub Releases API 호출
            url = f'https://api.github.com/repos/{repo}/releases'
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                releases = response.json()
                for release in releases[:10]:  # 최근 10개만
                    if release['tag_name'].startswith('backup-'):
                        for asset in release.get('assets', []):
                            if asset['name'].endswith('.json.gz'):
                                backup_history.append({
                                    'filename': asset['name'],
                                    'size': f"{asset['size'] / 1024:.1f} KB",
                                    'date': release['created_at'][:19].replace('T', ' '),
                                    'download_count': asset['download_count']
                                })
                        break  # 각 릴리스당 하나의 asset만
    except Exception as e:
        print(f"GitHub 백업 히스토리 로드 실패: {e}")
    
    # DB에서 복원 히스토리 가져오기
    restore_history = RestoreHistory.objects.all()[:10]  # 최근 10개
    
    context = {
        'backup_history': backup_history,
        'restore_history': restore_history,
    }
    return render(request, 'centers/backup_dashboard.html', context)

@user_passes_test(is_superuser)
@csrf_exempt
def perform_backup(request):
    """백업 실행"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청입니다.'})
    
    try:
        # 백업 명령어 실행
        output = StringIO()
        call_command('backup_data', storage='github', stdout=output)
        
        output_text = output.getvalue()
        
        # 백업 성공시 히스토리 저장
        try:
            # 파일명 추출 (출력에서)
            lines = output_text.split('\n')
            filename = None
            for line in lines:
                if 'backup_' in line and '.json.gz' in line:
                    # "=== 백업 완료: backup_20231201_143000.json.gz ===" 형태에서 파일명 추출
                    if '===' in line:
                        filename = line.split('===')[1].strip().replace('백업 완료: ', '').strip()
                        break
            
            if not filename:
                # 기본 파일명 생성
                from datetime import datetime
                filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json.gz"
            
            # 백업 히스토리 저장
            BackupHistory.objects.create(
                filename=filename,
                file_size=0,  # GitHub에서 실제 크기를 가져올 수 없으므로 0으로 설정
                backup_type='github',
                status='success',
                models_count={
                    'Center': Center.objects.count(),
                    'Review': Review.objects.count(),
                    'ExternalReview': ExternalReview.objects.count(),
                    'Therapist': Therapist.objects.count(),
                    'CenterImage': CenterImage.objects.count(),
                },
                created_by=request.user
            )
        except Exception as e:
            print(f"백업 히스토리 저장 실패: {e}")
        
        return JsonResponse({
            'success': True, 
            'message': '백업이 성공적으로 완료되었습니다.',
            'output': output_text
        })
    except Exception as e:
        # 백업 실패시 히스토리 저장
        try:
            BackupHistory.objects.create(
                filename=f"failed_backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
                file_size=0,
                backup_type='github',
                status='failed',
                models_count={},
                created_by=request.user,
                error_message=str(e)
            )
        except Exception as save_error:
            print(f"실패 히스토리 저장 실패: {save_error}")
        
        return JsonResponse({
            'success': False, 
            'error': f'백업 실행 중 오류가 발생했습니다: {str(e)}'
        })

@user_passes_test(is_superuser)
@csrf_exempt
def perform_restore(request):
    """복원 실행"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청입니다.'})
    
    if 'backup_file' not in request.FILES:
        return JsonResponse({'success': False, 'error': '백업 파일이 필요합니다.'})
    
    backup_file = request.FILES['backup_file']
    
    # 파일 이름 검증
    if not backup_file.name.endswith('.json.gz'):
        return JsonResponse({'success': False, 'error': '올바른 백업 파일 형식이 아닙니다. (.json.gz 파일만 허용)'})
    
    try:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json.gz') as temp_file:
            for chunk in backup_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        try:
            # 복원 명령어 실행
            output = StringIO()
            call_command('restore_data', temp_file_path, storage='local', force=True, stdout=output)
            
            output_text = output.getvalue()
            
            # 복원 성공시 히스토리 저장
            try:
                RestoreHistory.objects.create(
                    filename=backup_file.name,
                    file_size=backup_file.size,
                    restore_type='local',
                    status='success',
                    models_restored={
                        'restored_from': backup_file.name,
                        'file_size_mb': round(backup_file.size / (1024*1024), 2)
                    },
                    restored_by=request.user
                )
            except Exception as e:
                print(f"복원 히스토리 저장 실패: {e}")
            
            return JsonResponse({
                'success': True,
                'message': '복원이 성공적으로 완료되었습니다.',
                'output': output_text
            })
        except Exception as restore_error:
            # 복원 실패시 히스토리 저장
            try:
                RestoreHistory.objects.create(
                    filename=backup_file.name,
                    file_size=backup_file.size,
                    restore_type='local',
                    status='failed',
                    models_restored={},
                    restored_by=request.user,
                    error_message=str(restore_error)
                )
            except Exception as save_error:
                print(f"실패 히스토리 저장 실패: {save_error}")
            
            raise restore_error  # 원래 에러를 다시 발생시킴
        finally:
            # 임시 파일 삭제
            os.unlink(temp_file_path)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'복원 실행 중 오류가 발생했습니다: {str(e)}'
        })

@user_passes_test(is_superuser)
def get_backup_status(request):
    """백업 상태 조회"""
    try:
        output = StringIO()
        call_command('list_backups', storage='github', limit=5, stdout=output)
        
        return JsonResponse({
            'success': True,
            'backups': output.getvalue()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from .models import Center, Review, ExternalReview, Therapist, CenterImage, ReviewComment, BackupHistory, RestoreHistory
from .forms import ReviewForm, CenterManagementForm, TherapistManagementForm, ReviewCommentForm
from .utils import upload_image_to_cloudinary, delete_image_from_cloudinary  # Cloudinary 유틸리티 추가
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
from django.apps import apps

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
    # Cloudinary URL이 있으면 우선 사용, 없으면 로컬 이미지 URL 사용
    photo_url = None
    if therapist.photo_url:  # Cloudinary URL이 있는 경우
        photo_url = therapist.photo_url
    elif therapist.photo:  # 로컬 이미지가 있는 경우
        photo_url = therapist.photo.url
    
    return {
        'name': escape_quotes(therapist.name),
        'photo': escape_quotes(photo_url) if photo_url else None,
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
        
        # 센터 이미지 URL 처리 - Cloudinary URL 우선 사용
        image_urls = []
        for image in center.images.all():
            if image.image_url:  # Cloudinary URL이 있는 경우
                image_urls.append(escape_quotes(image.image_url))
            elif image.image:  # 로컬 이미지가 있는 경우
                image_urls.append(escape_quotes(image.image.url))
        
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
            'images': image_urls,
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
def home(request):
    """새로운 메인 홈페이지 뷰"""
    # 최신 리뷰 5개 가져오기
    latest_reviews = Review.objects.select_related('center', 'user').order_by('-created_at')[:5]
    
    # 자유게시판, 익명게시판, 이벤트게시판 최신 글 5개씩 가져오기 (boards 앱에서)
    try:
        from boards.models import Post
        free_posts = Post.objects.filter(board_type='free').order_by('-created_at')[:5]
        anonymous_posts = Post.objects.filter(board_type='anonymous').order_by('-created_at')[:5]
        event_posts = Post.objects.filter(board_type='event').select_related('event_detail').order_by('-created_at')[:5]
    except ImportError:
        free_posts = []
        anonymous_posts = []
        event_posts = []
    
    return render(request, 'centers/home.html', {
        'latest_reviews': latest_reviews,
        'free_posts': free_posts,
        'anonymous_posts': anonymous_posts,
        'event_posts': event_posts,
    })

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
    center = get_object_or_404(Center, id=center_id)
    page = int(request.GET.get('page', 1))
    per_page = 5  # 페이지당 5개 리뷰
    
    reviews = center.reviews.all().prefetch_related('comments').order_by('-created_at')
    paginator = Paginator(reviews, per_page)
    page_obj = paginator.get_page(page)
    
    reviews_data = [serialize_review(review, request.user) for review in page_obj]
    
    return JsonResponse({
        'reviews': reviews_data,
        'pagination': create_pagination_data(page_obj)
    })

def get_review_detail(request, review_id):
    """리뷰 상세 정보를 제공하는 API endpoint"""
    try:
        review = get_object_or_404(Review, id=review_id)
        
        review_data = {
            'id': review.id,
            'title': review.title,
            'content': review.content,
            'author': review.user.username,
            'rating': review.rating,
            'created_at': review.created_at.strftime('%Y년 %m월 %d일'),
            'center_name': review.center.name,
        }
        
        return JsonResponse({
            'success': True,
            'review': review_data
        })
    except Review.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '리뷰를 찾을 수 없습니다.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
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
                
                # 삭제될 상담사들의 Cloudinary 이미지 정리 (미리 파악)
                therapists_to_delete = []
                for form_instance in therapist_formset:
                    if form_instance.cleaned_data.get('DELETE') and form_instance.instance.pk:
                        therapists_to_delete.append(form_instance.instance)
                
                for therapist in therapists_to_delete:
                    if hasattr(therapist, 'photo_url') and therapist.photo_url:
                        print(f"🗑️ 상담사 사진 Cloudinary 삭제: {therapist.name}")
                        try:
                            # public_id 추출 방법 개선
                            if 'cloudinary.com' in therapist.photo_url:
                                url_parts = therapist.photo_url.split('/')
                                # therapists/filename.jpg에서 therapists/filename 추출
                                public_id_with_extension = '/'.join(url_parts[-2:])  # therapists/filename.jpg
                                public_id = public_id_with_extension.split('.')[0]  # therapists/filename
                                delete_result = delete_image_from_cloudinary(public_id)
                                print(f"✅ Cloudinary 삭제 결과: {delete_result}")
                        except Exception as e:
                            print(f"⚠️ Cloudinary 삭제 실패: {e}")
                
                # 삭제될 센터 이미지들의 Cloudinary 이미지 정리 (미리 파악)
                images_to_delete = []
                for form_instance in image_formset:
                    if form_instance.cleaned_data.get('DELETE') and form_instance.instance.pk:
                        images_to_delete.append(form_instance.instance)
                
                for center_image in images_to_delete:
                    if hasattr(center_image, 'image_url') and center_image.image_url:
                        print(f"🗑️ 센터 이미지 Cloudinary 삭제: {self.object.name}")
                        try:
                            # public_id 추출 방법 개선
                            if 'cloudinary.com' in center_image.image_url:
                                url_parts = center_image.image_url.split('/')
                                # centers/filename.jpg에서 centers/filename 추출
                                public_id_with_extension = '/'.join(url_parts[-2:])  # centers/filename.jpg
                                public_id = public_id_with_extension.split('.')[0]  # centers/filename
                                delete_result = delete_image_from_cloudinary(public_id)
                                print(f"✅ Cloudinary 삭제 결과: {delete_result}")
                        except Exception as e:
                            print(f"⚠️ Cloudinary 삭제 실패: {e}")
                
                # 상담사 폼셋 처리 (사진 Cloudinary 업로드)
                therapist_formset.instance = self.object
                therapist_instances = therapist_formset.save(commit=False)
                
                for therapist in therapist_instances:
                    # 새로운 사진이 업로드된 경우 Cloudinary에 저장
                    if therapist.photo:
                        print(f"🏥 상담사 사진 Cloudinary 업로드: {therapist.name}")
                        upload_result = upload_image_to_cloudinary(therapist.photo, folder='therapists')
                        
                        if upload_result.get('success') and upload_result.get('url'):
                            therapist.photo_url = upload_result['url']
                            print(f"✅ 상담사 사진 Cloudinary 업로드 성공: {upload_result['url']}")
                        else:
                            print(f"⚠️ 상담사 사진 Cloudinary 업로드 실패, 로컬 저장소 사용: {upload_result.get('error', '알 수 없는 오류')}")
                    
                    therapist.save()
                
                # 상담사 폼셋 최종 저장 (삭제 처리 포함)
                therapist_formset.save()
                
                # 센터 이미지 폼셋 처리 (Cloudinary 업로드)
                image_formset.instance = self.object
                image_instances = image_formset.save(commit=False)
                
                for center_image in image_instances:
                    # 새로운 이미지가 업로드된 경우 Cloudinary에 저장
                    if center_image.image:
                        print(f"🏢 센터 이미지 Cloudinary 업로드: {self.object.name}")
                        upload_result = upload_image_to_cloudinary(center_image.image, folder='centers')
                        
                        if upload_result.get('success') and upload_result.get('url'):
                            center_image.image_url = upload_result['url']
                            print(f"✅ 센터 이미지 Cloudinary 업로드 성공: {upload_result['url']}")
                        else:
                            print(f"⚠️ 센터 이미지 Cloudinary 업로드 실패, 로컬 저장소 사용: {upload_result.get('error', '알 수 없는 오류')}")
                    
                    center_image.save()
                
                # 이미지 폼셋 최종 저장 (삭제 처리 포함)
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
                    'ReviewComment': ReviewComment.objects.count(),
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
    
    data_file = request.FILES.get('backup_data')
    media_file = request.FILES.get('backup_media')
    
    if not data_file and not media_file:
        return JsonResponse({'success': False, 'error': '복원할 파일이 필요합니다.'})
    
    try:
        restored_data = {}
        
        # 데이터 파일 복원
        if data_file:
            if not data_file.name.endswith('.json.gz'):
                return JsonResponse({'success': False, 'error': '올바른 데이터 파일 형식이 아닙니다. (.json.gz 파일만 허용)'})
            
            restored_data.update(restore_data_file(data_file, request.user))
        
        # 미디어 파일 복원
        if media_file:
            if not media_file.name.endswith('.tar.gz'):
                return JsonResponse({'success': False, 'error': '올바른 미디어 파일 형식이 아닙니다. (.tar.gz 파일만 허용)'})
            
            restored_data.update(restore_media_file(media_file))
        
        # 복원 히스토리 저장
        try:
            RestoreHistory.objects.create(
                filename=f"data:{data_file.name if data_file else 'None'}, media:{media_file.name if media_file else 'None'}",
                file_size=(data_file.size if data_file else 0) + (media_file.size if media_file else 0),
                restore_type='complete' if (data_file and media_file) else ('data' if data_file else 'media'),
                status='success',
                restored_by=request.user,
                models_restored=restored_data.get('models_restored', {}),
                media_files_count=restored_data.get('media_files_count', 0)
            )
        except Exception as e:
            print(f"복원 히스토리 저장 실패: {e}")
        
        return JsonResponse({
            'success': True, 
            'message': '복원이 성공적으로 완료되었습니다.',
            'restored_data': restored_data
        })
        
    except Exception as e:
        # 복원 실패시 히스토리 저장
        try:
            RestoreHistory.objects.create(
                filename=f"data:{data_file.name if data_file else 'None'}, media:{media_file.name if media_file else 'None'}",
                file_size=(data_file.size if data_file else 0) + (media_file.size if media_file else 0),
                restore_type='complete' if (data_file and media_file) else ('data' if data_file else 'media'),
                status='failed',
                restored_by=request.user,
                error_message=str(e)
            )
        except Exception as save_error:
            print(f"실패 히스토리 저장 실패: {save_error}")
        
        return JsonResponse({
            'success': False, 
            'error': f'복원 실행 중 오류가 발생했습니다: {str(e)}'
        })

def restore_data_file(data_file, user):
    """데이터 파일을 복원합니다"""
    import gzip
    import json
    from django.core import serializers
    from django.db import transaction
    
    # 임시 파일로 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json.gz') as temp_file:
        for chunk in data_file.chunks():
            temp_file.write(chunk)
        temp_file_path = temp_file.name
    
    try:
        # 압축 해제 및 JSON 로드
        with gzip.open(temp_file_path, 'rt', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        models_restored = {}
        
        with transaction.atomic():
            # 메타데이터 확인
            if '_metadata' in backup_data:
                metadata = backup_data['_metadata']
                print(f"백업 정보: {metadata}")
            
            # 모델별 데이터 복원
            for model_name, model_data in backup_data.items():
                if model_name.startswith('_'):  # 메타데이터 스킵
                    continue
                
                try:
                    # 기존 데이터 삭제 (선택적)
                    model_class = apps.get_model('centers', model_name)
                    
                    # 데이터 복원
                    restored_objects = []
                    for obj_data in model_data['data']:
                        try:
                            # Django serializer를 사용해 객체 복원
                            for obj in serializers.deserialize('json', json.dumps([obj_data])):
                                obj.save()
                                restored_objects.append(obj.object)
                        except Exception as e:
                            print(f"객체 복원 실패: {e}")
                            continue
                    
                    models_restored[model_name] = len(restored_objects)
                    print(f"{model_name}: {len(restored_objects)}개 객체 복원 완료")
                
                except Exception as e:
                    print(f"{model_name} 모델 복원 실패: {e}")
                    continue
        
        return {
            'models_restored': models_restored,
            'total_restored': sum(models_restored.values())
        }
        
    finally:
        # 임시 파일 정리
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

def restore_media_file(media_file):
    """미디어 파일을 복원합니다"""
    import tarfile
    import shutil
    
    # 임시 파일로 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz') as temp_file:
        for chunk in media_file.chunks():
            temp_file.write(chunk)
        temp_file_path = temp_file.name
    
    try:
        media_root = settings.MEDIA_ROOT
        os.makedirs(media_root, exist_ok=True)
        
        restored_files = []
        
        # tar.gz 파일 추출
        with tarfile.open(temp_file_path, 'r:gz') as tar:
            for member in tar.getmembers():
                if member.isfile():
                    # 파일 추출
                    tar.extract(member, media_root)
                    restored_files.append(member.name)
                    print(f"미디어 파일 복원: {member.name}")
        
        return {
            'media_files_count': len(restored_files),
            'restored_files': restored_files[:10]  # 처음 10개만 반환
        }
        
    except Exception as e:
        print(f"미디어 파일 복원 실패: {e}")
        raise e
        
    finally:
        # 임시 파일 정리
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

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
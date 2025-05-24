from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Center, Review, ExternalReview
from .forms import ReviewForm
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
    return {
        'id': getattr(review, 'id', None),
        'title': escape_quotes(review.title),
        'content': escape_quotes(getattr(review, 'content', '')),
        'author': escape_quotes(review.user.username if hasattr(review, 'user') and review.user else '익명'),
        'rating': getattr(review, 'rating', 5),
        'created_at': format_date_for_json(review.created_at),
        'is_owner': user and hasattr(review, 'user') and review.user == user
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
            'reviews': [serialize_review(r, user) for r in center.reviews.all().order_by('-created_at')],
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
    centers = Center.objects.all().prefetch_related('images', 'therapists', 'reviews', 'external_reviews')
    
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
    reviews = Review.objects.filter(center=center).order_by('-created_at')
    
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
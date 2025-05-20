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

def index(request):
    centers = Center.objects.all().prefetch_related('images', 'therapists', 'reviews', 'external_reviews')

    center_list = []
    for center in centers:
        try:
            # Decimal 타입을 float로 변환
            lat = float(center.latitude) if isinstance(center.latitude, Decimal) else center.latitude
            lng = float(center.longitude) if isinstance(center.longitude, Decimal) else center.longitude
            
            # 상담사 정보 추가
            therapists_data = [{
                'name': therapist.name,
                'photo': therapist.photo.url if therapist.photo else None,
                'experience': therapist.experience,
                'specialty': therapist.specialty,
                'description': therapist.description
            } for therapist in center.therapists.all()]
            
            # 내부 리뷰 정보 추가
            reviews_data = [{
                'title': review.title,
                'content': review.content,
                'author': review.user.username if review.user else '익명',
                'rating': review.rating,
                'created_at': review.created_at.isoformat() if hasattr(review.created_at, 'isoformat') else review.created_at.strftime('%Y-%m-%d')
            } for review in center.reviews.all().order_by('-created_at')]
            
            # 외부 리뷰 정보 추가
            external_reviews_data = [{
                'title': review.title,
                'summary': review.summary,
                'source': review.source,
                'url': review.url,
                'created_at': review.created_at.isoformat() if hasattr(review.created_at, 'isoformat') else review.created_at.strftime('%Y-%m-%d')
            } for review in center.external_reviews.all().order_by('-created_at')]
            
            # 문자열 필드에서 따옴표 처리
            def escape_quotes(text):
                if text is None:
                    return ""
                return str(text).replace('"', '\\"').replace("'", "\\'")
            
            center_data = {
                'id': center.id,
                'name': escape_quotes(center.name),
                'lat': lat,
                'lng': lng,
                'address': escape_quotes(center.address),
                'phone': escape_quotes(center.phone),
                'url': escape_quotes(center.url),
                'operating_hours': escape_quotes(center.operating_hours),
                'description': escape_quotes(center.description),
                'images': [escape_quotes(image.image.url) for image in center.images.all()],
                'therapists': [{
                    'name': escape_quotes(t['name']),
                    'photo': escape_quotes(t['photo']),
                    'experience': t['experience'],
                    'specialty': escape_quotes(t['specialty']),
                    'description': escape_quotes(t['description'])
                } for t in therapists_data],
                'reviews': [{
                    'title': escape_quotes(r['title']),
                    'content': escape_quotes(r['content']),
                    'author': escape_quotes(r['author']),
                    'rating': r['rating'],
                    'created_at': escape_quotes(r['created_at'])
                } for r in reviews_data],
                'external_reviews': [{
                    'title': escape_quotes(r['title']),
                    'summary': escape_quotes(r['summary']),
                    'source': escape_quotes(r['source']),
                    'url': escape_quotes(r['url']),
                    'created_at': escape_quotes(r['created_at'])
                } for r in external_reviews_data],
                'is_authenticated': request.user.is_authenticated
            }
            center_list.append(center_data)
        except Exception as e:
            print(f"Error processing center {center.id}: {str(e)}")
            continue

    selected_center_id = request.GET.get('center_id')
    
    # JSON 형식으로 데이터 전달
    centers_json = json.dumps(center_list, ensure_ascii=False)
    selected_center_id_json = json.dumps(selected_center_id) if selected_center_id else 'null'
    is_authenticated_json = json.dumps(request.user.is_authenticated)
    
    return render(request, 'centers/index.html', {
        'centers_json': centers_json,
        'selected_center_id_json': selected_center_id_json,
        'is_authenticated_json': is_authenticated_json,
        'naver_client_id': settings.NAVER_CLIENT_ID
    })

def get_reviews(request, center_id):
    center = get_object_or_404(Center, pk=center_id)
    reviews = Review.objects.filter(center=center).order_by('-created_at')
    
    # 페이지네이션 설정
    page_number = request.GET.get('page', 1)
    paginator = Paginator(reviews, 10)  # 페이지당 10개의 리뷰
    page_obj = paginator.get_page(page_number)
    
    reviews_data = [
        {
            'id': review.id,
            'title': review.title, 
            'content': review.content,
            'author': review.user.username if review.user else '익명',
            'rating': review.rating,
            'created_at': review.created_at.isoformat() if hasattr(review.created_at, 'isoformat') else review.created_at.strftime('%Y-%m-%d'),
            'is_owner': request.user.is_authenticated and review.user == request.user
        }
        for review in page_obj
    ]
    
    # 페이지네이션 정보 추가
    pagination_data = {
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
    }
    
    return JsonResponse({
        'reviews': reviews_data,
        'pagination': pagination_data
    })

def center_detail(request, center_id):
    center = Center.objects.get(pk=center_id)
    reviews = Review.objects.filter(center=center).order_by('-date')

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')  # Redirect to login if user is not authenticated
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

    # Pass the center images to the template
    center_images = center.images.all()

    return render(request, 'centers/center_detail.html', {
        'center': center,
        'reviews': reviews,
        'form': form,
        'center_images': center_images,  # Pass the images to the template
    })

    
@login_required
def add_review(request, center_id):
    center = get_object_or_404(Center, pk=center_id)
    
    if request.method == 'POST':
        try:
            # JSON 데이터 파싱
            data = json.loads(request.body)
            title = data.get('title')
            content = data.get('content')
            rating = data.get('rating')
            
            if not title or not content or not rating:
                return JsonResponse({'error': '제목, 내용, 평점은 필수입니다.'}, status=400)
            
            try:
                rating = int(rating)
                if not (1 <= rating <= 5):
                    raise ValueError
            except (TypeError, ValueError):
                return JsonResponse({'error': '평점은 1에서 5 사이의 숫자여야 합니다.'}, status=400)
            
            # 리뷰 생성
            review = Review.objects.create(
                user=request.user,
                center=center,
                title=title,
                content=content,  # content 필드 사용
                rating=rating,
                created_at=timezone.now()
            )
            
            return JsonResponse({
                'success': True,
                'review': {
                    'id': review.id,
                    'title': review.title,
                    'content': review.content,  # content 필드 사용
                    'author': request.user.username,
                    'rating': review.rating,
                    'created_at': review.created_at.isoformat()
                }
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)

def search_results(request):
    query = request.GET.get('q', '')
    centers = []
    
    if query:
        # 검색어가 있는 경우 centers 모델에서 검색
        centers = Center.objects.filter(
            Q(name__icontains=query) |
            Q(address__icontains=query) |
            Q(phone__icontains=query) |  # phone 대신 contact 필드 사용
            Q(description__icontains=query)
        ).distinct()
    
    context = {
        'query': query,
        'centers': centers,
    }
    
    return render(request, 'centers/search_results.html', context)

def check_auth(request):
    """사용자의 인증 상태를 확인하는 API 엔드포인트"""
    return JsonResponse({
        'is_authenticated': request.user.is_authenticated
    })

@csrf_exempt
def geocode_address(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            address = data.get('address')
            
            if not address:
                return JsonResponse({'error': '주소가 필요합니다.'}, status=400)
            
            # 네이버 지도 API 호출
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
    
    return JsonResponse({'error': '잘못된 요청입니다.'}, status=400)

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
    
    # 페이지네이션 설정
    page_number = request.GET.get('page', 1)
    paginator = Paginator(external_reviews, 10)  # 페이지당 10개의 리뷰
    page_obj = paginator.get_page(page_number)
    
    reviews_data = [
        {
            'id': review.id,
            'title': review.title,
            'content': review.content,
            'source': review.source,
            'created_at': review.created_at.isoformat() if hasattr(review.created_at, 'isoformat') else review.created_at.strftime('%Y-%m-%d')
        }
        for review in page_obj
    ]
    
    # 페이지네이션 정보 추가
    pagination_data = {
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
    }
    
    return JsonResponse({
        'reviews': reviews_data,
        'pagination': pagination_data
    })

@login_required
def update_review(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    
    # 리뷰 작성자만 수정 가능
    if review.user != request.user:
        return JsonResponse({'error': '리뷰 수정 권한이 없습니다.'}, status=403)
    
    if request.method == 'PATCH':
        try:
            data = json.loads(request.body)
            title = data.get('title')
            content = data.get('content')
            rating = data.get('rating')
            
            if not title or not content or not rating:
                return JsonResponse({'error': '제목, 내용, 평점은 필수입니다.'}, status=400)
            
            try:
                rating = int(rating)
                if not (1 <= rating <= 5):
                    raise ValueError
            except (TypeError, ValueError):
                return JsonResponse({'error': '평점은 1에서 5 사이의 숫자여야 합니다.'}, status=400)
            
            review.title = title
            review.content = content
            review.rating = rating
            review.save()
            
            return JsonResponse({
                'success': True,
                'review': {
                    'id': review.id,
                    'title': review.title,
                    'content': review.content,
                    'author': request.user.username,
                    'rating': review.rating,
                    'created_at': review.created_at.isoformat()
                }
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'PATCH 요청만 허용됩니다.'}, status=405)

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    
    # 리뷰 작성자만 삭제 가능
    if review.user != request.user:
        return JsonResponse({'error': '리뷰 삭제 권한이 없습니다.'}, status=403)
    
    if request.method == 'DELETE':
        try:
            review.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'DELETE 요청만 허용됩니다.'}, status=405)

def upload_centers(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        decoded_file = csv_file.read().decode('utf-8')
        
        # CSV 파서 설정 - 따옴표 처리를 위한 옵션 추가
        csv_reader = csv.DictReader(
            decoded_file.splitlines(),
            quotechar='"',  # 큰따옴표를 인용 문자로 사용
            escapechar='\\',  # 이스케이프 문자 설정
            doublequote=True  # 큰따옴표를 두 번 사용하여 이스케이프
        )
        
        for row in csv_reader:
            try:
                # 주소로 위도/경도 가져오기
                geocode_result = geocode_address(row['address'])
                if not geocode_result:
                    continue
                
                # description에서 작은따옴표 처리
                description = row['description'].replace("'", "''") if row['description'] else ""
                
                # Center 객체 생성
                center = Center.objects.create(
                    name=row['name'],
                    address=row['address'],
                    phone=row['phone'],
                    url=row['url'],
                    description=description,
                    latitude=geocode_result['latitude'],
                    longitude=geocode_result['longitude']
                )
                
                # 이미지 URL이 있는 경우 처리
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
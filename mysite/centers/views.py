from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Center, Review
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

def index(request):
    centers = Center.objects.all().prefetch_related('images', 'therapists')

    center_list = []
    for center in centers:
        # Decimal 타입을 float로 변환
        lat = float(center.latitude) if isinstance(center.latitude, Decimal) else center.latitude
        lng = float(center.longitude) if isinstance(center.longitude, Decimal) else center.longitude
        
        # 상담사 정보 추가
        therapists_data = [{
            'name': therapist.name,
            'photo': therapist.photo.url if therapist.photo else None,
            'experience': therapist.experience,
            'specialty': therapist.specialty
        } for therapist in center.therapists.all()]
        
        center_data = {
            'id': center.id,
            'name': center.name,
            'lat': lat,
            'lng': lng,
            'address': center.address,
            'contact': center.contact,
            'url': center.url,
            'operating_hours': center.operating_hours,
            'description': center.description,
            'images': [image.image.url for image in center.images.all()],
            'therapists': therapists_data,
            'is_authenticated': request.user.is_authenticated
        }
        center_list.append(center_data)

    selected_center_id = request.GET.get('center_id')
    
    # JSON 형식으로 데이터 전달
    centers_json = json.dumps(center_list)
    selected_center_id_json = json.dumps(selected_center_id) if selected_center_id else 'null'
    is_authenticated_json = json.dumps(request.user.is_authenticated)
    
    return render(request, 'index.html', {
        'centers_json': centers_json,
        'selected_center_id_json': selected_center_id_json,
        'is_authenticated_json': is_authenticated_json,
        'naver_client_id': settings.NAVER_CLIENT_ID
    })

def center_list(request):
    centers = Center.objects.all().prefetch_related('images')
    center_list = []
    
    for center in centers:
        lat = float(center.latitude) if isinstance(center.latitude, Decimal) else center.latitude
        lng = float(center.longitude) if isinstance(center.longitude, Decimal) else center.longitude
        
        center_data = {
            'id': center.id,
            'name': center.name,
            'lat': lat,
            'lng': lng,
            'address': center.address,
            'contact': center.contact,
            'url': center.url,
            'operating_hours': center.operating_hours,
            'description': center.description,
            'images': [image.image.url for image in center.images.all()],
            'is_authenticated': request.user.is_authenticated
        }
        center_list.append(center_data)
    
    return JsonResponse({'centers': center_list})

def get_reviews(request, center_id):
    center = get_object_or_404(Center, pk=center_id)
    reviews = Review.objects.filter(center=center).order_by('-date')
    
    # 페이지네이션 설정
    page_number = request.GET.get('page', 1)
    paginator = Paginator(reviews, 10)  # 페이지당 10개의 리뷰
    page_obj = paginator.get_page(page_number)
    
    reviews_data = [
        {
            'id': review.id,
            'title': review.title, 
            'content': review.summary, 
            'author': review.user.username if review.user else '익명',
            'created_at': review.date.isoformat() if hasattr(review.date, 'isoformat') else review.date.strftime('%Y-%m-%d')
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
            
            if not title or not content:
                return JsonResponse({'error': '제목과 내용은 필수입니다.'}, status=400)
            
            # 리뷰 생성
            review = Review.objects.create(
                user=request.user,
                center=center,
                title=title,
                summary=content,  # content를 summary 필드에 저장
                date=timezone.now()
            )
            
            return JsonResponse({
                'success': True,
                'review': {
                    'id': review.id,
                    'title': review.title,
                    'content': review.summary,
                    'author': request.user.username,
                    'created_at': review.date.isoformat()
                }
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    # GET 요청 처리
    return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)

def search_results(request):
    query = request.GET.get('q', '')
    centers = []
    
    if query:
        # 검색어가 있는 경우 centers 모델에서 검색
        centers = Center.objects.filter(
            Q(name__icontains=query) |
            Q(address__icontains=query) |
            Q(contact__icontains=query) |  # phone 대신 contact 필드 사용
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
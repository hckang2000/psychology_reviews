from django.contrib import admin
from django.db import models
from django import forms
from .models import Center, Review, Therapist, CenterImage, ExternalReview
from django.conf import settings
import requests
import csv
import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import path
from django.http import HttpResponseRedirect, JsonResponse
from django.db import transaction
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import zipfile
from PIL import Image
import io
import tempfile
from datetime import datetime

# Inline for managing images within the Center admin
class CenterImageInline(admin.TabularInline):
    model = CenterImage
    extra = 1  # Number of extra blank image forms to show
    fields = ['image']  # Only show the image field

class TherapistInline(admin.TabularInline):
    model = Therapist
    extra = 1  # Number of extra blank therapist forms to show

class CenterAdminForm(forms.ModelForm):
    class Meta:
        model = Center
        fields = '__all__'
        widgets = {
            'address': forms.TextInput(attrs={
                'class': 'vLargeTextField',
                'placeholder': '주소를 입력하면 자동으로 위도/경도가 변환됩니다.'
            }),
            'latitude': forms.NumberInput(attrs={
                'readonly': 'readonly',
                'class': 'readonly-field'
            }),
            'longitude': forms.NumberInput(attrs={
                'readonly': 'readonly',
                'class': 'readonly-field'
            }),
        }

    class Media:
        js = ('centers/admin/js/geocoding.js',)
        css = {
            'all': ('centers/admin/css/admin.css',)
        }

class CsvImportForm(forms.Form):
    csv_file = forms.FileField(label='CSV 파일')
    image_zip = forms.FileField(label='이미지 ZIP 파일', required=False, help_text='선택사항: 상담소 이미지를 ZIP 파일로 업로드')

class TherapistCsvImportForm(forms.Form):
    csv_file = forms.FileField(label='CSV 파일')
    image_zip = forms.FileField(label='이미지 ZIP 파일', required=False, help_text='선택사항: 상담사 이미지를 ZIP 파일로 업로드')
    center = forms.ModelChoiceField(
        queryset=Center.objects.all(),
        label='상담소 선택',
        help_text='상담사를 등록할 상담소를 선택해주세요'
    )

class ExternalReviewCsvImportForm(forms.Form):
    csv_file = forms.FileField(label='CSV 파일')
    center = forms.ModelChoiceField(
        queryset=Center.objects.all(),
        label='상담소 선택',
        help_text='외부 리뷰를 등록할 상담소를 선택해주세요'
    )

@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    form = CenterAdminForm
    list_display = ('name', 'address', 'phone', 'url', 'created_at')
    search_fields = ('name', 'address')
    list_filter = ('created_at',)
    inlines = [TherapistInline, CenterImageInline]  # Display therapists and images inline
    readonly_fields = ('latitude', 'longitude')
    change_list_template = 'centers/admin/center_changelist.html'
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'address', 'phone', 'url')
        }),
        ('위치 정보', {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        ('상세 정보', {
            'fields': ('created_at', 'description'),
            'classes': ('collapse',)
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.import_csv, name='centers_center_import_csv'),
            path('import-csv/progress/', self.import_csv_progress, name='import-csv-progress'),
        ]
        return custom_urls + urls

    def import_csv_progress(self, request):
        if request.method == 'GET':
            progress = request.session.get('import_progress', {'total': 0, 'processed': 0})
            return JsonResponse(progress)
        return JsonResponse({'error': 'Invalid request method'})

    def get_geocode(self, address):
        try:
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
                    return first_result['y'], first_result['x']
            return None, None
        except Exception as e:
            return None, None

    def process_image_zip(self, zip_file, center_name, therapist_name=None):
        try:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                for filename in zip_ref.namelist():
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        # 이미지 파일 읽기
                        image_data = zip_ref.read(filename)
                        
                        # 이미지 유효성 검사
                        try:
                            Image.open(io.BytesIO(image_data))
                        except:
                            continue
                            
                        # 파일 저장 경로 설정
                        if therapist_name:
                            file_path = f'therapists/{center_name}/{therapist_name}/{filename}'
                        else:
                            file_path = f'centers/{center_name}/{filename}'
                            
                        # 디렉토리 생성
                        os.makedirs(os.path.dirname(os.path.join(settings.MEDIA_ROOT, file_path)), exist_ok=True)
                        
                        # 파일 저장
                        default_storage.save(file_path, ContentFile(image_data))
                        
                        return file_path
            return None
        except Exception as e:
            print(f"이미지 처리 중 오류: {str(e)}")
            return None

    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES.get("csv_file")
            image_zip = request.FILES.get("image_zip")
            
            if not csv_file:
                messages.error(request, 'CSV 파일을 선택해주세요.')
                return HttpResponseRedirect("..")
                
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'CSV 파일만 업로드 가능합니다.')
                return HttpResponseRedirect("..")
            
            try:
                # CSV 파일을 바이트로 읽기
                csv_content = csv_file.read().decode('utf-8-sig')
                
                # CSV 리더 설정 - 따옴표로 묶인 데이터 처리
                csv_reader = csv.DictReader(
                    csv_content.splitlines(),
                    quoting=csv.QUOTE_ALL,  # 모든 필드를 따옴표로 처리
                    skipinitialspace=True  # 따옴표 안의 공백 유지
                )
                
                # 데이터 행 읽기
                data_rows = list(csv_reader)
                
                if not data_rows:
                    raise ValueError('CSV 파일에 유효한 데이터가 없습니다.')
                
                print("CSV 필드명:", csv_reader.fieldnames)
                print("첫 번째 행 데이터:", data_rows[0])
                
                # 필수 필드 확인
                required_fields = ['name', 'address']
                for row in data_rows:
                    for field in required_fields:
                        if field not in row or not row[field].strip():
                            print(f"필드 누락 확인 - 필드명: {field}, 값: {row.get(field)}")
                            raise ValueError(f'필수 필드 {field}가 누락되었습니다.')
                
                # 중복 주소 검사
                addresses = [row['address'].strip() for row in data_rows]
                duplicate_addresses = set([x for x in addresses if addresses.count(x) > 1])
                if duplicate_addresses:
                    raise ValueError(f'중복된 주소가 있습니다: {", ".join(duplicate_addresses)}')
                
                # 기존 상담소 주소와 비교
                existing_addresses = set(Center.objects.values_list('address', flat=True))
                duplicate_existing = set(addresses) & existing_addresses
                if duplicate_existing:
                    raise ValueError(f'이미 등록된 상담소 주소가 있습니다: {", ".join(duplicate_existing)}')
                
                # Initialize progress tracking
                request.session['import_progress'] = {
                    'total': len(data_rows),
                    'processed': 0,
                    'success': 0,
                    'errors': []
                }
                
                # Process rows in batches
                batch_size = 10
                for i in range(0, len(data_rows), batch_size):
                    batch = data_rows[i:i + batch_size]
                    with transaction.atomic():
                        for row in batch:
                            try:
                                # Get geocode
                                latitude, longitude = self.get_geocode(row['address'])
                                
                                # Create center
                                center = Center(
                                    name=row['name'].strip(),
                                    address=row['address'].strip(),
                                    phone=row.get('phone', '').strip(),
                                    url=row.get('url', '').strip(),
                                    description=row.get('description', '').strip(),
                                    operating_hours=row.get('operating_hours', '').strip(),
                                    latitude=latitude,
                                    longitude=longitude
                                )
                                center.save()
                                print(f"상담소 생성 성공: {center.name}")
                                
                                # Process center images if zip file is provided
                                if image_zip and row.get('image_filename'):
                                    image_path = self.process_image_zip(image_zip, center.name)
                                    if image_path:
                                        CenterImage.objects.create(
                                            center=center,
                                            image=image_path
                                        )
                                        print(f"상담소 이미지 생성 성공: {image_path}")
                                
                                request.session['import_progress']['success'] += 1
                            except Exception as e:
                                print(f"오류 발생: {str(e)}")
                                request.session['import_progress']['errors'].append({
                                    'row': i + batch.index(row) + 1,
                                    'error': str(e)
                                })
                            
                            request.session['import_progress']['processed'] += 1
                            request.session.modified = True
                
                # Final success message
                success_count = request.session['import_progress']['success']
                error_count = len(request.session['import_progress']['errors'])
                messages.success(
                    request,
                    f'CSV 파일이 성공적으로 업로드되었습니다. (성공: {success_count}, 실패: {error_count})'
                )
                
                # Clear progress data
                del request.session['import_progress']
                
            except Exception as e:
                print(f"전체 처리 중 오류 발생: {str(e)}")
                messages.error(request, f'CSV 파일 처리 중 오류가 발생했습니다: {str(e)}')
            
            return HttpResponseRedirect("..")
        
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "centers/admin/csv_form.html", payload
        )

    def save_model(self, request, obj, form, change):
        if not obj.latitude or not obj.longitude:
            try:
                # 네이버 지도 API를 사용하여 주소를 좌표로 변환
                headers = {
                    'X-NCP-APIGW-API-KEY-ID': settings.NAVER_CLIENT_ID,
                    'X-NCP-APIGW-API-KEY': settings.NAVER_CLIENT_SECRET
                }
                response = requests.get(
                    f'https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode',
                    params={'query': obj.address},
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('addresses'):
                        first_result = result['addresses'][0]
                        obj.latitude = first_result['y']
                        obj.longitude = first_result['x']
            except Exception as e:
                self.message_user(request, f'주소 변환 중 오류가 발생했습니다: {str(e)}', level='ERROR')
        
        super().save_model(request, obj, form, change)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'center', 'user', 'rating', 'date')
    search_fields = ('title', 'content')
    list_filter = ('center', 'user', 'rating', 'date')

@admin.register(Therapist)
class TherapistAdmin(admin.ModelAdmin):
    list_display = ('name', 'center', 'specialty', 'created_at')
    search_fields = ('name', 'specialty')
    list_filter = ('center', 'created_at')
    change_list_template = 'centers/admin/therapist_changelist.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.import_csv, name='centers_therapist_import_csv'),
            path('import-csv/progress/', self.import_csv_progress, name='therapist-import-csv-progress'),
        ]
        return custom_urls + urls

    def import_csv_progress(self, request):
        if request.method == 'GET':
            progress = request.session.get('import_progress', {'total': 0, 'processed': 0})
            return JsonResponse(progress)
        return JsonResponse({'error': 'Invalid request method'})

    def process_image_zip(self, zip_file, center_name, therapist_name):
        try:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                for filename in zip_ref.namelist():
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        # 이미지 파일 읽기
                        image_data = zip_ref.read(filename)
                        
                        # 이미지 유효성 검사
                        try:
                            Image.open(io.BytesIO(image_data))
                        except:
                            continue
                            
                        # 파일 저장 경로 설정
                        file_path = f'therapists/{center_name}/{therapist_name}/{filename}'
                            
                        # 디렉토리 생성
                        os.makedirs(os.path.dirname(os.path.join(settings.MEDIA_ROOT, file_path)), exist_ok=True)
                        
                        # 파일 저장
                        default_storage.save(file_path, ContentFile(image_data))
                        
                        return file_path
            return None
        except Exception as e:
            print(f"이미지 처리 중 오류: {str(e)}")
            return None

    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES.get("csv_file")
            image_zip = request.FILES.get("image_zip")
            center_id = request.POST.get("center")
            
            print("=== CSV 업로드 시작 ===")
            print(f"CSV 파일: {csv_file}")
            print(f"이미지 ZIP: {image_zip}")
            print(f"상담소 ID: {center_id}")
            
            if not csv_file:
                print("오류: CSV 파일이 없습니다.")
                return JsonResponse({'error': 'CSV 파일을 선택해주세요.'}, status=400)
                
            if not csv_file.name.endswith('.csv'):
                print("오류: CSV 파일 형식이 아닙니다.")
                return JsonResponse({'error': 'CSV 파일만 업로드 가능합니다.'}, status=400)
            
            if not center_id:
                print("오류: 상담소가 선택되지 않았습니다.")
                return JsonResponse({'error': '상담소를 선택해주세요.'}, status=400)
            
            try:
                center = Center.objects.get(id=center_id)
                print(f"선택된 상담소: {center.name}")
                
                # CSV 파일을 바이트로 읽기
                csv_content = csv_file.read().decode('utf-8-sig')
                
                # CSV 리더 설정 - 따옴표로 묶인 데이터 처리
                csv_reader = csv.DictReader(
                    csv_content.splitlines(),
                    quoting=csv.QUOTE_ALL,  # 모든 필드를 따옴표로 처리
                    skipinitialspace=True  # 따옴표 안의 공백 유지
                )
                
                # 데이터 행 읽기
                data_rows = list(csv_reader)
                
                if not data_rows:
                    print("오류: CSV 파일에 유효한 데이터가 없습니다.")
                    return JsonResponse({'error': 'CSV 파일에 유효한 데이터가 없습니다.'}, status=400)
                
                print("CSV 필드명:", csv_reader.fieldnames)
                print("첫 번째 행 데이터:", data_rows[0])
                
                # 필수 필드 확인
                required_fields = ['name']
                for row in data_rows:
                    for field in required_fields:
                        if field not in row or not row[field].strip():
                            print(f"오류: 필수 필드 {field}가 누락되었습니다.")
                            print(f"행 데이터: {row}")
                            return JsonResponse({'error': f'필수 필드 {field}가 누락되었습니다.'}, status=400)
                
                # Initialize progress tracking
                request.session['import_progress'] = {
                    'total': len(data_rows),
                    'processed': 0,
                    'success': 0,
                    'errors': []
                }
                print(f"처리할 총 행 수: {len(data_rows)}")
                
                # Process rows in batches
                batch_size = 10
                for i in range(0, len(data_rows), batch_size):
                    batch = data_rows[i:i + batch_size]
                    print(f"=== 배치 처리 시작 (행 {i+1} ~ {i+len(batch)}) ===")
                    with transaction.atomic():
                        for row in batch:
                            try:
                                print(f"상담사 생성 시도: {row['name']}")
                                # Create therapist
                                therapist = Therapist(
                                    center=center,
                                    name=row['name'].strip(),
                                    specialty=row.get('specialty', '').strip(),
                                    description=row.get('description', '').strip(),
                                    experience=int(row.get('experience', 0) or 0)
                                )
                                therapist.save()
                                print(f"상담사 생성 성공: {therapist.name}")
                                
                                # Process therapist image if exists
                                if image_zip and row.get('image_filename'):
                                    print(f"이미지 처리 시도: {row['image_filename']}")
                                    image_path = self.process_image_zip(
                                        image_zip, 
                                        center.name, 
                                        therapist.name
                                    )
                                    if image_path:
                                        therapist.photo = image_path
                                        therapist.save()
                                        print(f"이미지 처리 성공: {image_path}")
                                    else:
                                        print(f"이미지 처리 실패: {row['image_filename']}")
                                
                                request.session['import_progress']['success'] += 1
                            except Exception as e:
                                print(f"오류 발생: {str(e)}")
                                print(f"오류가 발생한 행: {row}")
                                request.session['import_progress']['errors'].append({
                                    'row': i + batch.index(row) + 1,
                                    'error': str(e)
                                })
                            
                            request.session['import_progress']['processed'] += 1
                            request.session.modified = True
                            print(f"진행 상황: {request.session['import_progress']['processed']}/{request.session['import_progress']['total']}")
                
                # Final success message
                success_count = request.session['import_progress']['success']
                error_count = len(request.session['import_progress']['errors'])
                print(f"처리 완료: 성공 {success_count}, 실패 {error_count}")
                
                response_data = {
                    'success': True,
                    'message': f'CSV 파일이 성공적으로 업로드되었습니다. (성공: {success_count}, 실패: {error_count})',
                    'redirect': '../'
                }
                
                # Clear progress data
                del request.session['import_progress']
                
                return JsonResponse(response_data)
                
            except Exception as e:
                print(f"전체 처리 중 오류 발생: {str(e)}")
                print(f"오류 상세 정보: {type(e).__name__}")
                import traceback
                print(traceback.format_exc())
                return JsonResponse({'error': f'CSV 파일 처리 중 오류가 발생했습니다: {str(e)}'}, status=500)
        
        form = TherapistCsvImportForm()
        payload = {"form": form}
        return render(
            request, "centers/admin/therapist_csv_form.html", payload
        )

@admin.register(ExternalReview)
class ExternalReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'center', 'source', 'created_at')
    search_fields = ('title', 'source')
    list_filter = ('center', 'source', 'created_at')
    change_list_template = 'centers/admin/external_review_changelist.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.import_csv, name='centers_external_review_import_csv'),
            path('import-csv/progress/', self.import_csv_progress, name='external-review-import-csv-progress'),
        ]
        return custom_urls + urls

    def import_csv_progress(self, request):
        if request.method == 'GET':
            progress = request.session.get('import_progress', {'total': 0, 'processed': 0})
            return JsonResponse(progress)
        return JsonResponse({'error': 'Invalid request method'})

    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES.get("csv_file")
            center_id = request.POST.get("center")
            
            print("=== CSV 업로드 시작 ===")
            print(f"CSV 파일: {csv_file}")
            print(f"상담소 ID: {center_id}")
            
            if not csv_file:
                print("오류: CSV 파일이 없습니다.")
                return JsonResponse({'error': 'CSV 파일을 선택해주세요.'}, status=400)
                
            if not csv_file.name.endswith('.csv'):
                print("오류: CSV 파일 형식이 아닙니다.")
                return JsonResponse({'error': 'CSV 파일만 업로드 가능합니다.'}, status=400)
            
            if not center_id:
                print("오류: 상담소가 선택되지 않았습니다.")
                return JsonResponse({'error': '상담소를 선택해주세요.'}, status=400)
            
            try:
                center = Center.objects.get(id=center_id)
                print(f"선택된 상담소: {center.name}")
                
                # CSV 파일을 바이트로 읽기
                csv_content = csv_file.read().decode('utf-8-sig')
                
                # CSV 리더 설정 - 따옴표로 묶인 데이터 처리
                csv_reader = csv.DictReader(
                    csv_content.splitlines(),
                    quoting=csv.QUOTE_ALL,  # 모든 필드를 따옴표로 처리
                    skipinitialspace=True  # 따옴표 안의 공백 유지
                )
                
                # 데이터 행 읽기
                data_rows = list(csv_reader)
                
                if not data_rows:
                    print("오류: CSV 파일에 유효한 데이터가 없습니다.")
                    return JsonResponse({'error': 'CSV 파일에 유효한 데이터가 없습니다.'}, status=400)
                
                print("CSV 필드명:", csv_reader.fieldnames)
                print("첫 번째 행 데이터:", data_rows[0])
                
                # 필수 필드 확인
                required_fields = ['title', 'url']
                for row in data_rows:
                    for field in required_fields:
                        if field not in row or not row[field].strip():
                            print(f"오류: 필수 필드 {field}가 누락되었습니다.")
                            print(f"행 데이터: {row}")
                            return JsonResponse({'error': f'필수 필드 {field}가 누락되었습니다.'}, status=400)
                
                # Initialize progress tracking
                request.session['import_progress'] = {
                    'total': len(data_rows),
                    'processed': 0,
                    'success': 0,
                    'errors': []
                }
                print(f"처리할 총 행 수: {len(data_rows)}")
                
                # Process rows in batches
                batch_size = 10
                for i in range(0, len(data_rows), batch_size):
                    batch = data_rows[i:i + batch_size]
                    print(f"=== 배치 처리 시작 (행 {i+1} ~ {i+len(batch)}) ===")
                    with transaction.atomic():
                        for row in batch:
                            try:
                                print(f"외부 리뷰 생성 시도: {row['title']}")
                                # Create external review
                                external_review = ExternalReview(
                                    center=center,
                                    title=row['title'].strip(),
                                    url=row['url'].strip(),
                                    summary=row.get('summary', '').strip(),
                                    source=row.get('source', '').strip(),
                                    likes=int(row.get('likes', 0) or 0),
                                    dislikes=int(row.get('dislikes', 0) or 0)
                                )

                                # created_at 처리
                                created_at = row.get('created_at', '').strip()
                                if created_at:
                                    try:
                                        # Django의 기본 datetime 모듈 사용
                                        external_review.created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                                    except ValueError as e:
                                        print(f"날짜 형식 오류: {created_at}")
                                        raise ValueError("날짜 형식이 올바르지 않습니다. YYYY-MM-DD HH:MM:SS 형식을 사용해주세요. (예: 2024-03-15 14:30:00)")

                                external_review.save()
                                print(f"외부 리뷰 생성 성공: {external_review.title}")
                                
                                request.session['import_progress']['success'] += 1
                            except Exception as e:
                                print(f"오류 발생: {str(e)}")
                                print(f"오류가 발생한 행: {row}")
                                request.session['import_progress']['errors'].append({
                                    'row': i + batch.index(row) + 1,
                                    'error': str(e)
                                })
                            
                            request.session['import_progress']['processed'] += 1
                            request.session.modified = True
                            print(f"진행 상황: {request.session['import_progress']['processed']}/{request.session['import_progress']['total']}")
                
                # Final success message
                success_count = request.session['import_progress']['success']
                error_count = len(request.session['import_progress']['errors'])
                print(f"처리 완료: 성공 {success_count}, 실패 {error_count}")
                
                response_data = {
                    'success': True,
                    'message': f'CSV 파일이 성공적으로 업로드되었습니다. (성공: {success_count}, 실패: {error_count})',
                    'redirect': '../'
                }
                
                # Clear progress data
                del request.session['import_progress']
                
                return JsonResponse(response_data)
                
            except Exception as e:
                print(f"전체 처리 중 오류 발생: {str(e)}")
                print(f"오류 상세 정보: {type(e).__name__}")
                import traceback
                print(traceback.format_exc())
                return JsonResponse({'error': f'CSV 파일 처리 중 오류가 발생했습니다: {str(e)}'}, status=500)
        
        form = ExternalReviewCsvImportForm()
        payload = {"form": form}
        return render(
            request, "centers/admin/external_review_csv_form.html", payload
        )

@admin.register(CenterImage)
class CenterImageAdmin(admin.ModelAdmin):
    list_display = ('center', 'image', 'created_at')
    list_filter = ('center', 'created_at')

from django.contrib import admin
from django.db import models
from django import forms
from .models import Center, Review, Therapist, CenterImage, ExternalReview, BackupHistory, RestoreHistory
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

# CSV Import Mixin - 공통 로직 분리
class CSVImportMixin:
    """CSV 업로드 공통 기능을 제공하는 Mixin"""
    
    def init_progress_tracking(self, request, total_rows):
        """진행 상황 추적 초기화"""
        request.session['import_progress'] = {
            'total': total_rows,
            'processed': 0,
            'success': 0,
            'errors': []
        }
    
    def update_progress(self, request, success=True, error_msg=None, row_num=None):
        """진행 상황 업데이트"""
        if success:
            request.session['import_progress']['success'] += 1
        else:
            request.session['import_progress']['errors'].append({
                'row': row_num,
                'error': error_msg
            })
        request.session['import_progress']['processed'] += 1
        request.session.modified = True
    
    def clear_progress(self, request):
        """진행 상황 데이터 정리"""
        if 'import_progress' in request.session:
            del request.session['import_progress']
    
    def validate_csv_file(self, csv_file):
        """CSV 파일 유효성 검사"""
        if not csv_file:
            raise ValueError('CSV 파일을 선택해주세요.')
        if not csv_file.name.endswith('.csv'):
            raise ValueError('CSV 파일만 업로드 가능합니다.')
    
    def read_csv_data(self, csv_file):
        """CSV 데이터 읽기"""
        csv_content = csv_file.read().decode('utf-8-sig')
        csv_reader = csv.DictReader(
            csv_content.splitlines(),
            quoting=csv.QUOTE_ALL,
            skipinitialspace=True
        )
        data_rows = list(csv_reader)
        if not data_rows:
            raise ValueError('CSV 파일에 유효한 데이터가 없습니다.')
        return data_rows, csv_reader.fieldnames
    
    def validate_required_fields(self, data_rows, required_fields):
        """필수 필드 검증"""
        for row in data_rows:
            for field in required_fields:
                if field not in row or not row[field].strip():
                    raise ValueError(f'필수 필드 {field}가 누락되었습니다.')
    
    def extract_images_from_zip(self, zip_file):
        """ZIP 파일에서 이미지를 딕셔너리로 추출"""
        image_dict = {}
        if zip_file:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                for filename in zip_ref.namelist():
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        image_data = zip_ref.read(filename)
                        # 이미지 유효성 검사
                        try:
                            Image.open(io.BytesIO(image_data))
                            image_dict[os.path.basename(filename)] = image_data
                        except:
                            continue
        return image_dict
    
    def save_image(self, image_data, file_path):
        """이미지 파일 저장"""
        os.makedirs(os.path.dirname(os.path.join(settings.MEDIA_ROOT, file_path)), exist_ok=True)
        default_storage.save(file_path, ContentFile(image_data))
        return file_path
    
    def process_batch(self, data_rows, batch_size=10):
        """배치 단위로 데이터 처리"""
        for i in range(0, len(data_rows), batch_size):
            yield i, data_rows[i:i + batch_size]
    
    def get_success_response(self, request):
        """성공 응답 생성"""
        progress = request.session.get('import_progress', {})
        success_count = progress.get('success', 0)
        error_count = len(progress.get('errors', []))
        
        return JsonResponse({
            'success': True,
            'message': f'CSV 파일이 성공적으로 업로드되었습니다. (성공: {success_count}, 실패: {error_count})',
            'redirect': '../'
        })

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
    list_display = ('name', 'type', 'address', 'phone', 'url', 'created_at')
    search_fields = ('name', 'address')
    list_filter = ('type', 'created_at',)
    inlines = [TherapistInline, CenterImageInline]  # Display therapists and images inline
    readonly_fields = ('latitude', 'longitude')
    change_list_template = 'centers/admin/center_changelist.html'
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'type', 'address', 'phone', 'url')
        }),
        ('운영 정보', {
            'fields': ('operating_hours',)
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

    def get_queryset(self, request):
        """사용자 권한에 따라 센터 목록을 필터링"""
        qs = super().get_queryset(request)
        
        # 슈퍼유저는 모든 센터 접근 가능
        if request.user.is_superuser:
            return qs
        
        # 프로필이 없는 경우 빈 쿼리셋 반환
        if not hasattr(request.user, 'profile'):
            return qs.none()
        
        profile = request.user.profile
        
        # 총관리자는 모든 센터 접근 가능
        if profile.is_admin():
            return qs
        
        # 센터운영자는 자신이 관리하는 센터만 접근 가능
        if profile.is_center_manager() and profile.managed_center:
            return qs.filter(id=profile.managed_center.id)
        
        # 일반 사용자는 접근 불가
        return qs.none()
    
    def has_add_permission(self, request):
        """센터 추가 권한 확인"""
        if request.user.is_superuser:
            return True
        
        if hasattr(request.user, 'profile'):
            return request.user.profile.is_admin()
        
        return False
    
    def has_change_permission(self, request, obj=None):
        """센터 수정 권한 확인"""
        if request.user.is_superuser:
            return True
        
        if not hasattr(request.user, 'profile'):
            return False
        
        profile = request.user.profile
        
        # 총관리자는 모든 센터 수정 가능
        if profile.is_admin():
            return True
        
        # 센터운영자는 자신이 관리하는 센터만 수정 가능
        if profile.is_center_manager() and obj:
            return profile.managed_center == obj
        
        return False
    
    def has_delete_permission(self, request, obj=None):
        """센터 삭제 권한 확인 (총관리자만 가능)"""
        if request.user.is_superuser:
            return True
        
        if hasattr(request.user, 'profile'):
            return request.user.profile.is_admin()
        
        return False

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
            processed_files = []
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
                        processed_files.append(file_path)
                        print(f"이미지 처리 성공: {file_path}")
            
            return processed_files
        except Exception as e:
            print(f"이미지 처리 중 오류: {str(e)}")
            return []

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
                                
                                # Process type field
                                type_value = row.get('type', '').strip()
                                if type_value == '정신건강의학과':
                                    center_type = 'clinic'
                                else:
                                    center_type = 'counseling'  # 기본값 또는 "심리상담센터"인 경우
                                
                                # Create center
                                center = Center(
                                    name=row['name'].strip(),
                                    type=center_type,
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
                                if image_zip:
                                    image_paths = self.process_image_zip(image_zip, center.name)
                                    for image_path in image_paths:
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

    def delete_queryset(self, request, queryset):
        """센터 삭제 시 연관된 데이터도 함께 삭제"""
        from django.db import connection
        
        # Foreign Key 제약 조건 임시 비활성화
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA foreign_keys = OFF;')
        
        try:
            for center in queryset:
                # 연관된 데이터 수 확인
                therapist_count = center.therapists.count()
                image_count = center.images.count()
                review_count = center.reviews.count()
                external_review_count = center.external_reviews.count()
                
                # 로그 출력
                print(f"센터 '{center.name}' 삭제 중...")
                print(f"  - 상담사: {therapist_count}개")
                print(f"  - 이미지: {image_count}개")
                print(f"  - 리뷰: {review_count}개")
                print(f"  - 외부 리뷰: {external_review_count}개")
                
                # 리뷰 댓글 먼저 삭제
                for review in center.reviews.all():
                    review.comments.all().delete()
                
                # 연관된 데이터 삭제
                center.therapists.all().delete()
                center.images.all().delete()
                center.reviews.all().delete()
                center.external_reviews.all().delete()
                
                # 센터 삭제
                center.delete()
                
                print(f"센터 '{center.name}' 삭제 완료")
                
        finally:
            # Foreign Key 제약 조건 다시 활성화
            with connection.cursor() as cursor:
                cursor.execute('PRAGMA foreign_keys = ON;')

    def delete_model(self, request, obj):
        """단일 센터 삭제 시 연관된 데이터도 함께 삭제"""
        from django.db import connection
        
        # Foreign Key 제약 조건 임시 비활성화
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA foreign_keys = OFF;')
        
        try:
            # 연관된 데이터 수 확인
            therapist_count = obj.therapists.count()
            image_count = obj.images.count()
            review_count = obj.reviews.count()
            external_review_count = obj.external_reviews.count()
            
            # 로그 출력
            print(f"센터 '{obj.name}' 삭제 중...")
            print(f"  - 상담사: {therapist_count}개")
            print(f"  - 이미지: {image_count}개")
            print(f"  - 리뷰: {review_count}개")
            print(f"  - 외부 리뷰: {external_review_count}개")
            
            # 리뷰 댓글 먼저 삭제
            for review in obj.reviews.all():
                review.comments.all().delete()
            
            # 연관된 데이터 삭제
            obj.therapists.all().delete()
            obj.images.all().delete()
            obj.reviews.all().delete()
            obj.external_reviews.all().delete()
            
            # 센터 삭제
            obj.delete()
            
            print(f"센터 '{obj.name}' 삭제 완료")
            
        finally:
            # Foreign Key 제약 조건 다시 활성화
            with connection.cursor() as cursor:
                cursor.execute('PRAGMA foreign_keys = ON;')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'center', 'user', 'rating', 'date')
    search_fields = ('title', 'content')
    list_filter = ('center', 'user', 'rating', 'date')

@admin.register(Therapist)
class TherapistAdmin(CSVImportMixin, admin.ModelAdmin):
    list_display = ('name', 'center', 'specialty', 'created_at')
    search_fields = ('name', 'specialty')
    list_filter = ('center', 'created_at')
    change_list_template = 'centers/admin/therapist_changelist.html'

    def get_queryset(self, request):
        """사용자 권한에 따라 상담사 목록을 필터링"""
        qs = super().get_queryset(request)
        
        # 슈퍼유저는 모든 상담사 접근 가능
        if request.user.is_superuser:
            return qs
        
        # 프로필이 없는 경우 빈 쿼리셋 반환
        if not hasattr(request.user, 'profile'):
            return qs.none()
        
        profile = request.user.profile
        
        # 총관리자는 모든 상담사 접근 가능
        if profile.is_admin():
            return qs
        
        # 센터운영자는 자신이 관리하는 센터의 상담사만 접근 가능
        if profile.is_center_manager() and profile.managed_center:
            return qs.filter(center=profile.managed_center)
        
        # 일반 사용자는 접근 불가
        return qs.none()
    
    def has_add_permission(self, request):
        """상담사 추가 권한 확인"""
        if request.user.is_superuser:
            return True
        
        if hasattr(request.user, 'profile'):
            profile = request.user.profile
            return profile.is_admin() or profile.is_center_manager()
        
        return False
    
    def has_change_permission(self, request, obj=None):
        """상담사 수정 권한 확인"""
        if request.user.is_superuser:
            return True
        
        if not hasattr(request.user, 'profile'):
            return False
        
        profile = request.user.profile
        
        # 총관리자는 모든 상담사 수정 가능
        if profile.is_admin():
            return True
        
        # 센터운영자는 자신이 관리하는 센터의 상담사만 수정 가능
        if profile.is_center_manager() and obj:
            return profile.managed_center == obj.center
        
        return False
    
    def has_delete_permission(self, request, obj=None):
        """상담사 삭제 권한 확인"""
        if request.user.is_superuser:
            return True
        
        if not hasattr(request.user, 'profile'):
            return False
        
        profile = request.user.profile
        
        # 총관리자는 모든 상담사 삭제 가능
        if profile.is_admin():
            return True
        
        # 센터운영자는 자신이 관리하는 센터의 상담사만 삭제 가능
        if profile.is_center_manager() and obj:
            return profile.managed_center == obj.center
        
        return False

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

    def create_therapist_from_row(self, row, center, image_dict):
        """CSV 행에서 상담사 객체 생성"""
        therapist = Therapist(
            center=center,
            name=row['name'].strip(),
            specialty=row.get('specialty', '').strip(),
            description=row.get('description', '').strip(),
            experience=int(row.get('experience', 0) or 0)
        )
        therapist.save()
        
        # 이미지 처리
        if row.get('image_filename') and image_dict:
            image_filename = row['image_filename']
            image_data = image_dict.get(image_filename)
            if image_data:
                file_path = f'therapists/{center.name}/{therapist.name}/{image_filename}'
                self.save_image(image_data, file_path)
                therapist.photo = file_path
                therapist.save()
                print(f"이미지 처리 성공: {file_path}")
            else:
                print(f"이미지 처리 실패: {image_filename}")
        
        return therapist

    def import_csv(self, request):
        if request.method != "POST":
            form = TherapistCsvImportForm()
            return render(request, "centers/admin/therapist_csv_form.html", {"form": form})
        
        try:
            # 파일 및 센터 검증
            csv_file = request.FILES.get("csv_file")
            image_zip = request.FILES.get("image_zip")
            center_id = request.POST.get("center")
            
            self.validate_csv_file(csv_file)
            if not center_id:
                raise ValueError('상담소를 선택해주세요.')
            
            center = Center.objects.get(id=center_id)
            
            # CSV 데이터 읽기 및 검증
            data_rows, fieldnames = self.read_csv_data(csv_file)
            self.validate_required_fields(data_rows, ['name'])
            
            # 이미지 추출
            image_dict = self.extract_images_from_zip(image_zip)
            
            # 진행 상황 추적 초기화
            self.init_progress_tracking(request, len(data_rows))
            
            # 배치 처리
            for i, batch in self.process_batch(data_rows):
                with transaction.atomic():
                    for row in batch:
                        try:
                            self.create_therapist_from_row(row, center, image_dict)
                            self.update_progress(request, success=True)
                        except Exception as e:
                            self.update_progress(request, success=False, 
                                               error_msg=str(e), 
                                               row_num=i + batch.index(row) + 1)
            
            # 성공 응답
            response = self.get_success_response(request)
            self.clear_progress(request)
            return response
            
        except Exception as e:
            return JsonResponse({'error': f'CSV 파일 처리 중 오류가 발생했습니다: {str(e)}'}, status=500)

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

    def get_queryset(self, request):
        """사용자 권한에 따라 센터 이미지 목록을 필터링"""
        qs = super().get_queryset(request)
        
        # 슈퍼유저는 모든 센터 이미지 접근 가능
        if request.user.is_superuser:
            return qs
        
        # 프로필이 없는 경우 빈 쿼리셋 반환
        if not hasattr(request.user, 'profile'):
            return qs.none()
        
        profile = request.user.profile
        
        # 총관리자는 모든 센터 이미지 접근 가능
        if profile.is_admin():
            return qs
        
        # 센터운영자는 자신이 관리하는 센터의 이미지만 접근 가능
        if profile.is_center_manager() and profile.managed_center:
            return qs.filter(center=profile.managed_center)
        
        # 일반 사용자는 접근 불가
        return qs.none()
    
    def has_add_permission(self, request):
        """센터 이미지 추가 권한 확인"""
        if request.user.is_superuser:
            return True
        
        if hasattr(request.user, 'profile'):
            profile = request.user.profile
            return profile.is_admin() or profile.is_center_manager()
        
        return False
    
    def has_change_permission(self, request, obj=None):
        """센터 이미지 수정 권한 확인"""
        if request.user.is_superuser:
            return True
        
        if not hasattr(request.user, 'profile'):
            return False
        
        profile = request.user.profile
        
        # 총관리자는 모든 센터 이미지 수정 가능
        if profile.is_admin():
            return True
        
        # 센터운영자는 자신이 관리하는 센터의 이미지만 수정 가능
        if profile.is_center_manager() and obj:
            return profile.managed_center == obj.center
        
        return False
    
    def has_delete_permission(self, request, obj=None):
        """센터 이미지 삭제 권한 확인"""
        if request.user.is_superuser:
            return True
        
        if not hasattr(request.user, 'profile'):
            return False
        
        profile = request.user.profile
        
        # 총관리자는 모든 센터 이미지 삭제 가능
        if profile.is_admin():
            return True
        
        # 센터운영자는 자신이 관리하는 센터의 이미지만 삭제 가능
        if profile.is_center_manager() and obj:
            return profile.managed_center == obj.center
        
        return False

@admin.register(BackupHistory)
class BackupHistoryAdmin(admin.ModelAdmin):
    list_display = ('filename', 'backup_type', 'status', 'file_size_kb', 'created_by', 'created_at')
    list_filter = ('backup_type', 'status', 'created_at')
    search_fields = ('filename', 'created_by__username')
    readonly_fields = ('filename', 'file_size', 'backup_type', 'status', 'models_count', 'created_by', 'created_at', 'error_message')
    
    def file_size_kb(self, obj):
        if obj.file_size:
            return f"{obj.file_size / 1024:.1f} KB"
        return "알 수 없음"
    file_size_kb.short_description = "파일 크기"
    
    def has_add_permission(self, request):
        return False  # 백업 히스토리는 시스템에서 자동 생성
    
    def has_change_permission(self, request, obj=None):
        return False  # 읽기 전용

@admin.register(RestoreHistory)
class RestoreHistoryAdmin(admin.ModelAdmin):
    list_display = ('filename', 'restore_type', 'status', 'file_size_kb', 'restored_by', 'created_at')
    list_filter = ('restore_type', 'status', 'created_at')
    search_fields = ('filename', 'restored_by__username')
    readonly_fields = ('filename', 'file_size', 'restore_type', 'status', 'models_restored', 'restored_by', 'created_at', 'error_message')
    
    def file_size_kb(self, obj):
        if obj.file_size:
            return f"{obj.file_size / 1024:.1f} KB"
        return "알 수 없음"
    file_size_kb.short_description = "파일 크기"
    
    def has_add_permission(self, request):
        return False  # 복원 히스토리는 시스템에서 자동 생성
    
    def has_change_permission(self, request, obj=None):
        return False  # 읽기 전용

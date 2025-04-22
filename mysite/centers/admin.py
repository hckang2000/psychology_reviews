from django.contrib import admin
from django.db import models
from django import forms
from .models import Center, Review, Therapist, CenterImage, ExternalReview
from django.conf import settings
import requests

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

@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    form = CenterAdminForm
    list_display = ('name', 'address', 'phone', 'created_at')
    search_fields = ('name', 'address')
    list_filter = ('created_at',)
    inlines = [TherapistInline, CenterImageInline]  # Display therapists and images inline
    readonly_fields = ('latitude', 'longitude')
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'address', 'phone')
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

@admin.register(ExternalReview)
class ExternalReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'center', 'source', 'created_at')
    search_fields = ('title', 'source')
    list_filter = ('center', 'source', 'created_at')

@admin.register(CenterImage)
class CenterImageAdmin(admin.ModelAdmin):
    list_display = ('center', 'image', 'created_at')
    list_filter = ('center', 'created_at')

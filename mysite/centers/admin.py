from django.contrib import admin
from .models import Center, Review, Therapist

class TherapistInline(admin.TabularInline):
    model = Therapist
    extra = 1  # 추가할 수 있는 기본 상담사 입력란 수

@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'contact', 'url', 'operating_hours')
    search_fields = ('name', 'address')
    inlines = [TherapistInline]  # 상담사 정보를 센터와 함께 관리

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('center', 'title', 'date')
    search_fields = ('center__name', 'title')
    list_filter = ('center', 'date')

@admin.register(Therapist)
class TherapistAdmin(admin.ModelAdmin):
    list_display = ('name', 'center', 'experience', 'specialty')
    search_fields = ('name', 'specialty')
    list_filter = ('center', 'specialty')
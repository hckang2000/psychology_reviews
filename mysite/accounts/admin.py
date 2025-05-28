from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = '프로필'
    fields = ('nickname', 'role', 'managed_center')

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'get_managed_center', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__role')
    
    def get_role(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.get_role_display()
        return '-'
    get_role.short_description = '권한'
    
    def get_managed_center(self, obj):
        if hasattr(obj, 'profile') and obj.profile.managed_center:
            return obj.profile.managed_center.name
        return '-'
    get_managed_center.short_description = '관리 센터'

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'nickname', 'role', 'managed_center')
    list_filter = ('role',)
    search_fields = ('user__username', 'nickname')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'managed_center')

# 기존 UserAdmin을 해제하고 새로운 CustomUserAdmin 등록
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

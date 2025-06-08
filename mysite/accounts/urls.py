from django.urls import path, include
from django.shortcuts import redirect
from .views import CustomLoginView, CustomSignupView, CustomConfirmEmailView, custom_logout, custom_email_verification_sent, CustomPasswordResetView, CustomPasswordResetDoneView, profile_update, account_delete

app_name = 'accounts'

def socialaccount_signup_redirect(request):
    """소셜 계정 가입 페이지를 홈으로 리다이렉트"""
    return redirect('centers:home')

urlpatterns = [
    path('confirm-email/', custom_email_verification_sent, name='account_email_verification_sent'),
    path('confirm-email/<str:key>/', CustomConfirmEmailView.as_view(), name='account_confirm_email'),
    path('login/', CustomLoginView.as_view(), name='account_login'),
    path('signup/', CustomSignupView.as_view(), name='account_signup'),
    path('password/reset/', CustomPasswordResetView.as_view(), name='account_reset_password'),
    path('password/reset/done/', CustomPasswordResetDoneView.as_view(), name='account_reset_password_done'),
    path('logout/', custom_logout, name='account_logout'),
    path('profile/', profile_update, name='profile_update'),
    path('delete/', account_delete, name='account_delete'),
    path('social/signup/', socialaccount_signup_redirect, name='socialaccount_signup'),
    path('', include('allauth.urls')),
]
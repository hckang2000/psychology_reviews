from django.urls import path, include
from .views import CustomLoginView, CustomSignupView, CustomConfirmEmailView, custom_logout, custom_email_verification_sent, CustomPasswordResetView, CustomPasswordResetDoneView

app_name = 'accounts'

urlpatterns = [
    path('confirm-email/', custom_email_verification_sent, name='account_email_verification_sent'),
    path('confirm-email/<str:key>/', CustomConfirmEmailView.as_view(), name='account_confirm_email'),
    path('login/', CustomLoginView.as_view(), name='account_login'),
    path('signup/', CustomSignupView.as_view(), name='account_signup'),
    path('password/reset/', CustomPasswordResetView.as_view(), name='account_reset_password'),
    path('password/reset/done/', CustomPasswordResetDoneView.as_view(), name='account_reset_password_done'),
    path('logout/', custom_logout, name='account_logout'),
    path('', include('allauth.urls')),
]
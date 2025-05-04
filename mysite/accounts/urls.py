from django.urls import path, include
from .views import CustomLoginView, CustomSignupView, CustomConfirmEmailView, logout

app_name = 'accounts'

urlpatterns = [
    path('', include('allauth.urls')),
    path('login/', CustomLoginView.as_view(), name='account_login'),
    path('signup/', CustomSignupView.as_view(), name='account_signup'),
    path('logout/', logout, name='account_logout'),
    path('confirm-email/<str:key>/', CustomConfirmEmailView.as_view(), name='account_confirm_email'),
]
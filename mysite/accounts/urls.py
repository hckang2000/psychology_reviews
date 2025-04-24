from django.urls import path, include
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', include('allauth.urls')),
    path('logout/', views.logout_view, name='logout'),
]
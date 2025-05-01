from django.urls import path, include
from . import views

urlpatterns = [
    path('', include('allauth.urls')),
    path('logout/', views.logout_view, name='logout'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search, name='search'),
    path('reviews/<int:center_id>/add/', views.add_review, name='add_review'),
]
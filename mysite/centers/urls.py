from django.urls import path
from . import views

app_name = 'centers'

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search_results, name='search_results'),
    path('api/centers/', views.center_list, name='center_list'),
    path('api/geocode/', views.geocode_address, name='geocode_address'),
    path('reviews/<int:center_id>/', views.get_reviews, name='get_reviews'),
    path('reviews/<int:center_id>/add/', views.add_review, name='add_review'),
    path('check-auth/', views.check_auth, name='check_auth'),
    path('<int:center_id>/', views.center_detail, name='center_detail'),
    path('review-form/<int:center_id>/', views.review_form, name='review_form'),
]
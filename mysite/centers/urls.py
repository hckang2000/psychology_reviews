from django.urls import path
from . import views

app_name = 'centers'

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search_results, name='search_results'),
    path('api/geocode/', views.geocode_address, name='geocode_address'),
    path('reviews/<int:center_id>/', views.get_reviews, name='get_reviews'),
    path('reviews/<int:review_id>/update/', views.update_review, name='update_review'),
    path('reviews/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    path('reviews/<int:center_id>/add/', views.add_review, name='add_review'),
    path('check-auth/', views.check_auth, name='check_auth'),
    path('<int:center_id>/', views.center_detail, name='center_detail'),
    path('review-form/<int:center_id>/', views.review_form, name='review_form'),
    
    # 센터 관리 URL
    path('management/', views.center_management_dashboard, name='management_dashboard'),
    path('management/centers/', views.CenterListView.as_view(), name='center_list_management'),
    path('management/center/<int:pk>/', views.CenterManagementView.as_view(), name='center_management'),
]
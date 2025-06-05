from django.urls import path
from . import views

app_name = 'centers'

urlpatterns = [
    path('', views.home, name='home'),  # 새로운 메인 페이지
    path('centers/', views.index, name='index'),  # 기존 index를 센터찾기 페이지로 변경
    path('search/', views.search_results, name='search_results'),
    path('api/geocode/', views.geocode_address, name='geocode_address'),
    path('reviews/<int:center_id>/', views.get_reviews, name='get_reviews'),
    path('reviews/<int:review_id>/update/', views.update_review, name='update_review'),
    path('reviews/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    path('reviews/<int:center_id>/add/', views.add_review, name='add_review'),
    path('api/review/<int:review_id>/', views.get_review_detail, name='get_review_detail'),
    path('check-auth/', views.check_auth, name='check_auth'),
    path('<int:center_id>/', views.center_detail, name='center_detail'),
    path('review-form/<int:center_id>/', views.review_form, name='review_form'),
    
    # 센터 관리 URL
    path('management/', views.center_management_dashboard, name='management_dashboard'),
    path('management/centers/', views.CenterListView.as_view(), name='center_list_management'),
    path('management/center/<int:pk>/', views.CenterManagementView.as_view(), name='center_management'),
    
    # 리뷰 관리 URL
    path('management/reviews/', views.ReviewManagementView.as_view(), name='review_management'),
    path('reviews/<int:review_id>/comments/', views.get_review_comments, name='get_review_comments'),
    path('reviews/<int:review_id>/comments/add/', views.add_review_comment, name='add_review_comment'),
    path('comments/<int:comment_id>/update/', views.update_review_comment, name='update_review_comment'),
    path('comments/<int:comment_id>/delete/', views.delete_review_comment, name='delete_review_comment'),
    
    # 백업/복원 URL (superuser 전용)
    path('backup/', views.backup_dashboard, name='backup_dashboard'),
    path('backup/perform/', views.perform_backup, name='perform_backup'),
    path('backup/restore/', views.perform_restore, name='perform_restore'),
    path('backup/status/', views.get_backup_status, name='get_backup_status'),
]
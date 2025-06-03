from django.urls import path
from . import views

app_name = 'boards'

urlpatterns = [
    # 게시판 목록
    path('free/', views.board_list, {'board_type': 'free'}, name='free_board'),
    path('anonymous/', views.board_list, {'board_type': 'anonymous'}, name='anonymous_board'),
    path('event/', views.board_list, {'board_type': 'event'}, name='event_board'),
    
    # 게시글 CRUD
    path('<str:board_type>/create/', views.post_create, name='post_create'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/<int:pk>/update/', views.post_update, name='post_update'),
    path('post/<int:pk>/delete/', views.post_delete, name='post_delete'),
    
    # 댓글
    path('post/<int:post_pk>/comment/', views.comment_create, name='comment_create'),
    path('comment/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
] 
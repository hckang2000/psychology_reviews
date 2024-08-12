from django.contrib import admin
from django.urls import path, include  # include is needed to include URLs from other apps
from centers import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('reviews/<int:center_id>/', views.get_reviews, name='get_reviews'),
    path('reviews/<int:center_id>/add/', views.add_review, name='add_review'),
    path('accounts/', include('accounts.urls')),  # Include the URLs from the accounts app
    path('accounts/', include('django.contrib.auth.urls')),  # For login/logout
    path('<int:center_id>/', views.center_detail, name='center_detail'),
]
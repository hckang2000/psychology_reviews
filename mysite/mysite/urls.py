from django.contrib import admin
from django.urls import path, include
from django.conf import settings  # Import settings
from django.conf.urls.static import static  # Import static for serving media files
from centers import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('centers.urls', namespace='centers')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('board/', include('boards.urls', namespace='boards')),
    path('reviews/<int:center_id>/', views.get_reviews, name='get_reviews'),
    path('reviews/<int:center_id>/add/', views.add_review, name='add_review'),
    path('<int:center_id>/', views.center_detail, name='center_detail'),
]

# Add static files (media)
if settings.DEBUG:  # Only serve media files in development mode
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

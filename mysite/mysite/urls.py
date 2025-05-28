from django.contrib import admin
from django.urls import path, include
from django.conf import settings  # Import settings
from django.conf.urls.static import static  # Import static for serving media files

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('', include('centers.urls', namespace='centers')),
    path('board/', include('boards.urls', namespace='boards')),
]

# Add static files (media)
if settings.DEBUG:  # Only serve media files in development mode
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

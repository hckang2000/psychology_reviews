"""
WSGI config for mysite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

application = get_wsgi_application()

# 운영환경(Render)에서만 WhiteNoise 사용
if os.getenv('RENDER'):
    try:
        from whitenoise import WhiteNoise
        application = WhiteNoise(application, root='staticfiles')
        application.add_files('static', prefix='static/')
        application.add_files('centers/static', prefix='centers/static/')
        application.add_files('boards/static', prefix='boards/static/')
    except ImportError:
        pass  # 로컬 환경에서 whitenoise가 없어도 무시

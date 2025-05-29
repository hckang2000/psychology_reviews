# Django가 시작될 때 Celery 앱이 로드되도록 설정 (선택적)
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery가 설치되지 않은 환경에서는 무시
    __all__ = ()

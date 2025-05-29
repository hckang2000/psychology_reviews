import os
from celery import Celery
from django.conf import settings

# Django 설정 모듈을 Celery에 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

app = Celery('mysite')

# Django 설정에서 Celery 설정 불러오기
app.config_from_object('django.conf:settings', namespace='CELERY')

# Django 앱들에서 task 자동 발견
app.autodiscover_tasks()

# 주기적 태스크 스케줄 설정
from celery.schedules import crontab

app.conf.beat_schedule = {
    'weekly-backup': {
        'task': 'centers.tasks.automated_backup',
        'schedule': crontab(hour=14, minute=0, day_of_week=0),  # 매주 일요일 14:00
    },
    'monthly-cleanup': {
        'task': 'centers.tasks.cleanup_old_backups',
        'schedule': crontab(hour=2, minute=0, day_of_month=1),  # 매월 1일 02:00
        'kwargs': {'keep_count': 10},
    },
}

app.conf.timezone = 'Asia/Seoul' 
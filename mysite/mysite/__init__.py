# Django 초기화 파일

from django.db.backends.signals import connection_created
from django.dispatch import receiver

@receiver(connection_created)
def activate_foreign_keys(sender, connection, **kwargs):
    """SQLite에서 Foreign Key 제약 조건 활성화"""
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON;')
        cursor.close()

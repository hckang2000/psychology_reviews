# Generated by Django 4.2.21 on 2025-05-29 01:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('centers', '0004_reviewcomment'),
    ]

    operations = [
        migrations.CreateModel(
            name='RestoreHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(help_text='복원된 백업 파일명', max_length=255)),
                ('file_size', models.BigIntegerField(help_text='파일 크기 (bytes)')),
                ('restore_type', models.CharField(default='local', help_text='복원 소스', max_length=50)),
                ('status', models.CharField(default='success', help_text='복원 상태', max_length=20)),
                ('models_restored', models.JSONField(default=dict, help_text='복원된 모델별 레코드 수')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('error_message', models.TextField(blank=True, help_text='오류 메시지 (실패시)')),
                ('restored_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '복원 히스토리',
                'verbose_name_plural': '복원 히스토리 목록',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='BackupHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(help_text='백업 파일명', max_length=255)),
                ('file_size', models.BigIntegerField(help_text='파일 크기 (bytes)')),
                ('backup_type', models.CharField(default='github', help_text='백업 저장 위치', max_length=50)),
                ('status', models.CharField(default='success', help_text='백업 상태', max_length=20)),
                ('models_count', models.JSONField(default=dict, help_text='모델별 백업 레코드 수')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('error_message', models.TextField(blank=True, help_text='오류 메시지 (실패시)')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '백업 히스토리',
                'verbose_name_plural': '백업 히스토리 목록',
                'ordering': ['-created_at'],
            },
        ),
    ]

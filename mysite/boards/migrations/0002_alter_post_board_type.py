# Generated by Django 5.0.2 on 2025-06-03 15:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boards', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='board_type',
            field=models.CharField(choices=[('free', '자유게시판'), ('anonymous', '익명게시판'), ('event', '이벤트게시판')], max_length=10, verbose_name='게시판 종류'),
        ),
    ]

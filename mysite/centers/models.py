from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

class Center(models.Model):
    # Type choices
    TYPE_CHOICES = [
        ('counseling', '심리상담센터'),
        ('clinic', '정신건강의학과'),
    ]
    
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, default='')
    url = models.URLField(blank=True, help_text='상담소 웹사이트 URL')
    description = models.TextField(blank=True)
    operating_hours = models.CharField(max_length=100, blank=True)
    type = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES, 
        default='counseling',
        help_text='상담소 유형을 선택하세요'
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '상담소'
        verbose_name_plural = '상담소 목록'
        ordering = ['-created_at']

class Therapist(models.Model):
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name='therapists')
    name = models.CharField(max_length=50)
    specialty = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='therapists/', blank=True, null=True)
    experience = models.PositiveIntegerField(default=0, help_text='상담사의 경력 연차')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.center.name}"

    class Meta:
        verbose_name = '상담사'
        verbose_name_plural = '상담사 목록'
        ordering = ['-created_at']

class Review(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField(default='')
    rating = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)])
    date = models.DateField(default=timezone.now)
    url = models.URLField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.title} - {self.center.name}"

    class Meta:
        verbose_name = '리뷰'
        verbose_name_plural = '리뷰 목록'
        ordering = ['-created_at']

class ReviewComment(models.Model):
    """센터관리자가 리뷰에 달 수 있는 댓글"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(help_text='댓글 내용을 입력하세요')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text='댓글 활성화 여부')

    def __str__(self):
        return f"{self.review.title}에 대한 {self.author.username}의 댓글"

    class Meta:
        verbose_name = '리뷰 댓글'
        verbose_name_plural = '리뷰 댓글 목록'
        ordering = ['created_at']

class ExternalReview(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField()
    summary = models.CharField(blank=True, max_length=100)
    source = models.CharField(blank=True, max_length=50)
    created_at = models.DateTimeField(default=timezone.now)
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name='external_reviews')

    def __str__(self):
        return f"{self.title} - {self.center.name}"

    class Meta:
        verbose_name = '외부 리뷰'
        verbose_name_plural = '외부 리뷰'
        ordering = ['-created_at']

class CenterImage(models.Model):
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='centers/')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.center.name} - {self.created_at}"

    class Meta:
        verbose_name = '상담소 이미지'
        verbose_name_plural = '상담소 이미지 목록'
        ordering = ['-created_at']

class BackupHistory(models.Model):
    """백업 히스토리"""
    filename = models.CharField(max_length=255, help_text='백업 파일명')
    file_size = models.BigIntegerField(help_text='파일 크기 (bytes)')
    backup_type = models.CharField(max_length=50, default='github', help_text='백업 저장 위치')
    status = models.CharField(max_length=20, default='success', help_text='백업 상태')
    models_count = models.JSONField(default=dict, help_text='모델별 백업 레코드 수')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    error_message = models.TextField(blank=True, help_text='오류 메시지 (실패시)')

    def __str__(self):
        return f"백업 {self.filename} - {self.created_at}"

    class Meta:
        verbose_name = '백업 히스토리'
        verbose_name_plural = '백업 히스토리 목록'
        ordering = ['-created_at']

class RestoreHistory(models.Model):
    """복원 히스토리"""
    filename = models.CharField(max_length=255, help_text='복원된 백업 파일명')
    file_size = models.BigIntegerField(help_text='파일 크기 (bytes)')
    restore_type = models.CharField(max_length=50, default='local', help_text='복원 소스')
    status = models.CharField(max_length=20, default='success', help_text='복원 상태')
    models_restored = models.JSONField(default=dict, help_text='복원된 모델별 레코드 수')
    media_files_count = models.IntegerField(default=0, help_text='복원된 미디어 파일 수')
    restored_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    error_message = models.TextField(blank=True, help_text='오류 메시지 (실패시)')

    def __str__(self):
        return f"복원 {self.filename} - {self.created_at}"

    class Meta:
        verbose_name = '복원 히스토리'
        verbose_name_plural = '복원 히스토리 목록'
        ordering = ['-created_at']

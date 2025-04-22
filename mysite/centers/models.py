from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

class Center(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, default='')
    url = models.URLField(blank=True, help_text='상담소 웹사이트 URL')
    description = models.TextField(blank=True)
    operating_hours = models.CharField(max_length=100, blank=True)
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

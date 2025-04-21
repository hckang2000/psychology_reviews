from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Center(models.Model):
    name = models.CharField(max_length=200, verbose_name='상담소 이름')
    address = models.CharField(max_length=500, verbose_name='주소')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='위도')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='경도')
    contact = models.CharField(max_length=100, verbose_name='연락처')
    url = models.URLField(blank=True, verbose_name='웹사이트')
    operating_hours = models.CharField(max_length=200, blank=True, verbose_name='운영시간')
    description = models.TextField(blank=True, verbose_name='설명')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = '상담소'
        verbose_name_plural = '상담소 목록'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class CenterImage(models.Model):
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name='images', verbose_name='상담소')
    image = models.ImageField(upload_to='centers/', verbose_name='이미지')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='생성일')

    class Meta:
        verbose_name = '상담소 이미지'
        verbose_name_plural = '상담소 이미지 목록'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.center.name} - {self.created_at}"

class Review(models.Model):
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name='reviews', verbose_name='상담소')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='작성자')
    title = models.CharField(max_length=200, verbose_name='제목')
    summary = models.TextField(verbose_name='내용')
    date = models.DateTimeField(auto_now_add=True, verbose_name='작성일')

    class Meta:
        verbose_name = '리뷰'
        verbose_name_plural = '리뷰 목록'
        ordering = ['-date']

    def __str__(self):
        return f"{self.center.name} - {self.title}"

class Therapist(models.Model):
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name='therapists', verbose_name='상담소')
    name = models.CharField(max_length=200, verbose_name='이름')
    photo = models.ImageField(upload_to='therapists/', blank=True, null=True, verbose_name='사진')
    experience = models.IntegerField(verbose_name='경력(년)')
    specialty = models.CharField(max_length=200, verbose_name='전문 분야')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = '상담사'
        verbose_name_plural = '상담사 목록'
        ordering = ['-experience']  # 경력이 많은 순서대로 정렬

    def __str__(self):
        return f"{self.name} ({self.specialty})"

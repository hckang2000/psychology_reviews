from django.db import models
from django.contrib.auth.models import User  # Import the User model

class Center(models.Model):
    name = models.CharField(max_length=200)
    representative = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    contact = models.CharField(max_length=100)
    url = models.URLField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    operating_hours = models.CharField(max_length=100)  # 운영시간
    description = models.TextField()  # 센터 소개글

    def __str__(self):
        return self.name

class Review(models.Model):
    center = models.ForeignKey(Center, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    summary = models.TextField()
    date = models.DateField()
    url = models.CharField(max_length=200, null=True, blank=True)  # Allow null and blank values

    def __str__(self):
        return self.title
    
    @property
    def has_url(self):
        return bool(self.url)

class Therapist(models.Model):
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name='therapists')
    name = models.CharField(max_length=200)  # 이름
    experience = models.IntegerField()  # 경력 (년수)
    specialty = models.CharField(max_length=200)  # 전문 분야

    def __str__(self):
        return f"{self.name} ({self.specialty})"
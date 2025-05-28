from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    ROLE_CHOICES = [
        ('admin', '총관리자'),
        ('center_manager', '센터운영자'),
        ('user', '일반회원'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=100)
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='user',
        help_text='사용자 권한을 선택하세요'
    )
    managed_center = models.ForeignKey(
        'centers.Center', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text='센터운영자인 경우 관리할 센터를 선택하세요'
    )

    class Meta:
        app_label = 'accounts'
        verbose_name = '사용자 프로필'
        verbose_name_plural = '사용자 프로필 목록'

    def __str__(self):
        return f"{self.nickname} ({self.get_role_display()})"
    
    def is_center_manager(self):
        """센터운영자인지 확인"""
        return self.role == 'center_manager'
    
    def is_admin(self):
        """총관리자인지 확인"""
        return self.role == 'admin'
    
    def can_manage_center(self, center):
        """특정 센터를 관리할 수 있는지 확인"""
        if self.is_admin():
            return True
        if self.is_center_manager() and self.managed_center == center:
            return True
        return False

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    elif not hasattr(instance, 'profile'):
        # For existing users who do not have a profile yet
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
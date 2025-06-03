from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

class Post(models.Model):
    BOARD_CHOICES = [
        ('free', '자유게시판'),
        ('anonymous', '익명게시판'),
        ('event', '이벤트게시판'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='제목')
    content = models.TextField(verbose_name='내용')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='작성자')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')
    board_type = models.CharField(max_length=10, choices=BOARD_CHOICES, verbose_name='게시판 종류')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = '게시글'
        verbose_name_plural = '게시글'
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('boards:post_detail', kwargs={'pk': self.pk})

class EventPost(models.Model):
    """이벤트 게시글 전용 모델 (Post 모델과 1:1 관계)"""
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='event_detail')
    price = models.CharField(max_length=100, verbose_name='가격', help_text='예: 무료, 10,000원, 50% 할인')
    start_date = models.DateTimeField(verbose_name='이벤트 시작일')
    end_date = models.DateTimeField(verbose_name='이벤트 종료일')
    
    class Meta:
        verbose_name = '이벤트 상세정보'
        verbose_name_plural = '이벤트 상세정보'
    
    def __str__(self):
        return f'{self.post.title} - {self.price}'
    
    @property
    def is_active(self):
        """이벤트가 현재 활성화 상태인지 확인"""
        now = timezone.now()
        return self.start_date <= now <= self.end_date
    
    @property
    def is_expired(self):
        """이벤트가 만료되었는지 확인"""
        return timezone.now() > self.end_date

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='게시글')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='작성자')
    content = models.TextField(verbose_name='내용')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일시')
    
    class Meta:
        ordering = ['created_at']
        verbose_name = '댓글'
        verbose_name_plural = '댓글'
    
    def __str__(self):
        return f'{self.author}의 댓글: {self.content[:20]}'

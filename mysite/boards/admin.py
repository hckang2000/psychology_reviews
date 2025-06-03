from django.contrib import admin
from .models import Post, Comment, EventPost

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'board_type', 'created_at']
    list_filter = ['board_type', 'created_at']
    search_fields = ['title', 'content', 'author__username']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'author', 'content', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'author__username']

@admin.register(EventPost)
class EventPostAdmin(admin.ModelAdmin):
    list_display = ['post', 'price', 'start_date', 'end_date', 'is_active']
    list_filter = ['start_date', 'end_date']
    search_fields = ['post__title', 'price']
    
    def is_active(self, obj):
        return obj.is_active
    is_active.boolean = True
    is_active.short_description = '활성상태'

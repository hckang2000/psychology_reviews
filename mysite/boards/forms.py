from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '제목을 입력하세요'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '내용을 입력하세요',
                'rows': 5
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        content = cleaned_data.get('content')
        
        # 비속어 필터링 (예시)
        bad_words = ['비속어1', '비속어2', '비속어3']  # 실제 비속어 목록으로 대체 필요
        
        for word in bad_words:
            if word in title or word in content:
                raise forms.ValidationError('비속어가 포함되어 있습니다.')
        
        return cleaned_data

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '댓글을 입력하세요',
                'rows': 3
            })
        }

    def clean_content(self):
        content = self.cleaned_data['content']
        
        # 비속어 필터링 (예시)
        bad_words = ['비속어1', '비속어2', '비속어3']  # 실제 비속어 목록으로 대체 필요
        
        for word in bad_words:
            if word in content:
                raise forms.ValidationError('비속어가 포함되어 있습니다.')
        
        return content 
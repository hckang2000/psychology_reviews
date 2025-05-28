from django import forms
from .models import Review, Center, Therapist, CenterImage

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['title', 'content', 'rating']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
        }

class CenterManagementForm(forms.ModelForm):
    """센터 관리자용 센터 정보 수정 폼"""
    
    class Meta:
        model = Center
        fields = ['name', 'type', 'address', 'phone', 'url', 'description', 'operating_hours']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '센터명을 입력하세요'
            }),
            'type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '주소를 입력하세요'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '전화번호를 입력하세요'
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': '웹사이트 URL을 입력하세요'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '센터 소개를 입력하세요'
            }),
            'operating_hours': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '운영시간을 입력하세요 (예: 평일 09:00-18:00)'
            }),
        }
        labels = {
            'name': '센터명',
            'type': '센터 유형',
            'address': '주소',
            'phone': '전화번호',
            'url': '웹사이트',
            'description': '센터 소개',
            'operating_hours': '운영시간',
        }

class TherapistManagementForm(forms.ModelForm):
    """상담사 관리 폼"""
    
    class Meta:
        model = Therapist
        fields = ['name', 'specialty', 'description', 'photo', 'experience']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '상담사명을 입력하세요'
            }),
            'specialty': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '전문분야를 입력하세요'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '상담사 소개를 입력하세요'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'experience': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '경력 연차'
            }),
        }
        labels = {
            'name': '상담사명',
            'specialty': '전문분야',
            'description': '상담사 소개',
            'photo': '사진',
            'experience': '경력 (년)',
        }
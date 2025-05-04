from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from allauth.account.forms import LoginForm, SignupForm

class CustomUserCreationForm(UserCreationForm):
    nickname = forms.CharField(max_length=100, required=True, help_text='Nickname')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'nickname']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super(CustomLoginForm, self).__init__(*args, **kwargs)
        self.fields['login'].widget.attrs.update({
            'class': 'form-input w-full',
            'placeholder': '아이디'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-input w-full',
            'placeholder': '비밀번호'
        })
        if 'remember_me' in self.fields:
            self.fields['remember_me'].widget.attrs.update({
                'class': 'h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded'
            })

class CustomSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super(CustomSignupForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-input w-full',
            'placeholder': '이메일'
        })
        self.fields['username'].widget.attrs.update({
            'class': 'form-input w-full',
            'placeholder': '아이디'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input w-full',
            'placeholder': '비밀번호'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input w-full',
            'placeholder': '비밀번호 확인'
        })
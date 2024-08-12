from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    nickname = forms.CharField(max_length=100, required=True, help_text='Nickname')

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'nickname')
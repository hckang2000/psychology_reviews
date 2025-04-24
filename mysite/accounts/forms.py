from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    nickname = forms.CharField(max_length=100, required=True, help_text='Nickname')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'nickname']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from allauth.account.views import LoginView

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('centers:index')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('centers:index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

class CustomLoginView(LoginView):
    def form_valid(self, form):
        user = form.user
        if user.is_superuser:
            login(self.request, user)
            return redirect(self.get_success_url())
        return super().form_valid(form)

@login_required
def logout_view(request):
    logout(request)
    return redirect('centers:index')
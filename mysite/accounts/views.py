from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from .forms import SignUpForm
from .models import Profile
from django.urls import reverse_lazy

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            nickname = form.cleaned_data.get('nickname')
            user.profile.nickname = nickname  # Save nickname to profile
            user.save()
            login(request, user)
            return redirect('centers:index')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        # Using reverse_lazy ensures the URL is correctly resolved and handled
        return reverse_lazy('centers:index')
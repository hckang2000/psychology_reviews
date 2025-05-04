from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from allauth.account.views import LoginView, SignupView, ConfirmEmailView
from allauth.account.utils import send_email_confirmation
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from .forms import CustomLoginForm, CustomSignupForm

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # admin 계정이거나 이미 이메일이 인증된 경우 바로 로그인
            if user.is_superuser or user.emailaddress_set.filter(verified=True).exists():
                login(request, user)
                return redirect('centers:index')
            # 일반 사용자이고 이메일이 인증되지 않은 경우
            messages.warning(request, '이메일 인증이 필요합니다. 이메일을 확인해주세요.')
            return redirect('account_login')
    else:
        form = AuthenticationForm()
    return render(request, 'account/login.html', {'form': form})

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # admin 계정인 경우 이메일 인증 없이 바로 로그인
            if user.is_superuser or user.username in ['admin', 'administrator']:
                user.emailaddress_set.create(
                    email=user.email,
                    primary=True,
                    verified=True
                )
                login(request, user)
                return redirect('centers:index')
            # 일반 사용자인 경우 이메일 인증 진행
            send_email_confirmation(request, user)
            messages.info(request, '이메일 인증 메일을 발송했습니다. 이메일을 확인해주세요.')
            return redirect('account_login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'account/signup.html', {'form': form})

class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = 'account/login.html'
    success_url = reverse_lazy('centers:index')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '로그인되었습니다.')
        return response

class CustomSignupView(SignupView):
    form_class = CustomSignupForm
    template_name = 'account/signup.html'
    success_url = reverse_lazy('centers:index')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '회원가입이 완료되었습니다. 이메일 인증을 완료해주세요.')
        return response

class CustomConfirmEmailView(ConfirmEmailView):
    template_name = 'account/email_confirm.html'
    
    def get(self, *args, **kwargs):
        print('[디버그] CustomConfirmEmailView.get() 호출됨 - account/email_confirm.html 사용')
        return super().get(*args, **kwargs)

@login_required
def logout(request):
    auth_logout(request)
    messages.success(request, '로그아웃되었습니다.')
    return redirect('centers:index')

def custom_email_verification_sent(request):
    print("==== [디버그] custom_email_verification_sent 뷰가 호출됨 ====")
    return render(request, 'account/email_verification_sent.html')
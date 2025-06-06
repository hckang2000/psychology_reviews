from django.shortcuts import render, redirect
from django.contrib.auth import login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, ProfileUpdateForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from allauth.account.views import LoginView, SignupView, ConfirmEmailView, PasswordResetView, PasswordResetDoneView
from allauth.account.utils import send_email_confirmation
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from .forms import CustomLoginForm, CustomSignupForm
from django.utils.translation import gettext as _
from django.http import JsonResponse

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # admin 계정이거나 이미 이메일이 인증된 경우 바로 로그인
            if user.is_superuser or user.emailaddress_set.filter(verified=True).exists():
                login(request, user)
                messages.success(request, f'{user.username}님, 환영합니다!')
                return redirect('centers:index')
            # 일반 사용자이고 이메일이 인증되지 않은 경우
            messages.warning(request, '이메일 인증이 필요합니다. 이메일을 확인해주세요.')
            return redirect('account_login')
        else:
            messages.error(request, '로그인에 실패했습니다. 아이디와 비밀번호를 확인해주세요.')
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
                messages.success(request, f'{user.username}님, 회원가입이 완료되었습니다!')
                return redirect('centers:index')
            # 일반 사용자인 경우 이메일 인증 진행
            send_email_confirmation(request, user)
            messages.success(request, '회원가입이 완료되었습니다. 이메일 인증 메일을 확인해주세요.')
            return redirect('account_login')
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{error}")
            messages.error(request, '회원가입에 실패했습니다. ' + ' '.join(error_messages))
    else:
        form = CustomUserCreationForm()
    return render(request, 'account/signup.html', {'form': form})

class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = 'account/login.html'
    success_url = reverse_lazy('centers:index')

    def form_valid(self, form):
        user = form.get_user()
        response = super().form_valid(form)
        messages.success(self.request, f'{user.username}님, 환영합니다!')
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        error_messages = []
        
        # 로그인 실패 원인을 상세히 분석
        login_field = form.cleaned_data.get('login', '')
        
        if form.errors:
            if 'login' in form.errors or 'password' in form.errors:
                if User.objects.filter(username=login_field).exists():
                    messages.error(self.request, '비밀번호가 올바르지 않습니다.')
                elif User.objects.filter(email=login_field).exists():
                    messages.error(self.request, '비밀번호가 올바르지 않습니다.')
                else:
                    messages.error(self.request, '존재하지 않는 계정입니다. 아이디 또는 이메일을 확인해주세요.')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        error_messages.append(str(error))
                if error_messages:
                    messages.error(self.request, '로그인에 실패했습니다: ' + ' '.join(error_messages))
        else:
            messages.error(self.request, '로그인에 실패했습니다. 입력 정보를 확인해주세요.')
        
        return response

class CustomSignupView(SignupView):
    form_class = CustomSignupForm
    template_name = 'account/signup.html'
    success_url = reverse_lazy('centers:index')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '회원가입이 완료되었습니다. 이메일 인증을 완료해주세요.')
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        error_messages = []
        
        # 회원가입 실패 원인을 상세히 분석
        for field_name, errors in form.errors.items():
            field_label = {
                'username': '아이디',
                'email': '이메일',
                'password1': '비밀번호',
                'password2': '비밀번호 확인'
            }.get(field_name, field_name)
            
            for error in errors:
                if 'already exists' in str(error) or '이미 사용 중' in str(error):
                    if field_name == 'username':
                        error_messages.append('이미 사용 중인 아이디입니다.')
                    elif field_name == 'email':
                        error_messages.append('이미 사용 중인 이메일입니다.')
                elif 'password' in field_name and 'common' in str(error):
                    error_messages.append('너무 일반적인 비밀번호입니다.')
                elif 'password' in field_name and 'short' in str(error):
                    error_messages.append('비밀번호가 너무 짧습니다. 최소 8자 이상이어야 합니다.')
                elif 'password2' in field_name and "didn't match" in str(error):
                    error_messages.append('비밀번호가 일치하지 않습니다.')
                else:
                    error_messages.append(f'{field_label}: {error}')
        
        if error_messages:
            messages.error(self.request, '회원가입에 실패했습니다. ' + ' '.join(error_messages))
        else:
            messages.error(self.request, '회원가입에 실패했습니다. 입력 정보를 확인해주세요.')
        
        return response

class CustomPasswordResetView(PasswordResetView):
    template_name = 'account/password_reset.html'
    success_url = reverse_lazy('account_reset_password_done')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '비밀번호 재설정 링크를 이메일로 발송했습니다. 이메일을 확인해주세요.')
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        error_messages = []
        
        for field, errors in form.errors.items():
            for error in errors:
                if 'email' in field and 'invalid' in str(error).lower():
                    error_messages.append('올바른 이메일 주소를 입력해주세요.')
                else:
                    error_messages.append(str(error))
        
        if error_messages:
            messages.error(self.request, '비밀번호 재설정 요청에 실패했습니다. ' + ' '.join(error_messages))
        else:
            messages.error(self.request, '비밀번호 재설정 요청에 실패했습니다. 이메일 주소를 확인해주세요.')
        
        return response

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'account/password_reset_done.html'

    def get(self, request, *args, **kwargs):
        # 이미 form_valid에서 메시지를 설정했으므로 여기서는 추가하지 않음
        return super().get(request, *args, **kwargs)

class CustomConfirmEmailView(ConfirmEmailView):
    template_name = 'account/email_confirm.html'
    
    def get(self, *args, **kwargs):
        print('[디버그] CustomConfirmEmailView.get() 호출됨 - account/email_confirm.html 사용')
        return super().get(*args, **kwargs)

@login_required
def custom_logout(request):
    username = request.user.username
    auth_logout(request)
    messages.success(request, f'{username}님, 안전하게 로그아웃되었습니다.')
    return redirect('centers:index')

def custom_email_verification_sent(request):
    print("==== [디버그] custom_email_verification_sent 뷰가 호출됨 ====")
    return render(request, 'account/email_verification_sent.html')

@login_required
def profile_update(request):
    """회원정보 수정 뷰"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            # 사용자명 중복 체크 (현재 사용자 제외)
            username = form.cleaned_data['username']
            if User.objects.filter(username=username).exclude(pk=request.user.pk).exists():
                messages.error(request, '이미 사용 중인 아이디입니다.')
                return render(request, 'account/profile_update.html', {'form': form})
            
            # 이메일 중복 체크 (현재 사용자 제외)
            email = form.cleaned_data['email']
            if User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
                messages.error(request, '이미 사용 중인 이메일입니다.')
                return render(request, 'account/profile_update.html', {'form': form})
            
            form.save()
            messages.success(request, '회원정보가 성공적으로 수정되었습니다.')
            return redirect('accounts:profile_update')
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(str(error))
            messages.error(request, '정보 수정에 실패했습니다. ' + ' '.join(error_messages))
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'account/profile_update.html', {'form': form})

@login_required
def account_delete(request):
    """회원탈퇴 뷰"""
    if request.method == 'POST':
        # POST 요청에 confirmation 파라미터가 있는지 확인
        if request.POST.get('confirmation') == 'delete':
            username = request.user.username
            # 회원탈퇴 처리
            request.user.delete()
            auth_logout(request)
            messages.success(request, f'{username}님의 계정이 성공적으로 삭제되었습니다. 그동안 이용해주셔서 감사했습니다.')
            return redirect('centers:home')
        else:
            messages.error(request, '회원탈퇴 확인이 필요합니다.')
            return redirect('accounts:profile_update')
    
    # GET 요청은 profile_update 페이지로 리다이렉트
    return redirect('accounts:profile_update')
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth.models import User
import uuid


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """소셜 로그인 사용자 정보 커스터마이징"""
    
    def is_auto_signup_allowed(self, request, sociallogin):
        """자동 가입 허용 - 모든 소셜 로그인에서 자동 가입"""
        return True
    
    def pre_social_login(self, request, sociallogin):
        """소셜 로그인 전 처리 - 기존 계정과 연결"""
        user = sociallogin.user
        if user.id:
            return
        
        # 이메일로 기존 사용자 찾기
        if user.email:
            try:
                existing_user = User.objects.get(email=user.email)
                sociallogin.connect(request, existing_user)
            except User.DoesNotExist:
                pass
    
    def populate_user(self, request, sociallogin, data):
        """소셜 로그인 사용자 정보 채우기"""
        user = super().populate_user(request, sociallogin, data)
        
        # 사용자명이 없으면 자동 생성
        if not user.username:
            # 이메일에서 사용자명 추출 시도
            if user.email:
                username_base = user.email.split('@')[0]
            else:
                username_base = f"{sociallogin.account.provider}_user"
            
            # 중복 확인 후 고유한 사용자명 생성
            username = username_base
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{username_base}_{counter}"
                counter += 1
            
            user.username = username
        
        # Google 로그인의 경우 추가 정보 설정
        if sociallogin.account.provider == 'google':
            extra_data = sociallogin.account.extra_data
            
            # 이름 정보 설정
            if not user.first_name and 'given_name' in extra_data:
                user.first_name = extra_data['given_name']
            
            if not user.last_name and 'family_name' in extra_data:
                user.last_name = extra_data['family_name']
                
            # 전체 이름으로 fallback
            if not user.first_name and not user.last_name and 'name' in extra_data:
                name_parts = extra_data['name'].split(' ', 1)
                user.first_name = name_parts[0]
                if len(name_parts) > 1:
                    user.last_name = name_parts[1]
        
        # 네이버 로그인의 경우
        elif sociallogin.account.provider == 'naver':
            extra_data = sociallogin.account.extra_data
            response = extra_data.get('response', {})
            
            if not user.first_name and 'name' in response:
                user.first_name = response['name']
        
        # 카카오 로그인의 경우
        elif sociallogin.account.provider == 'kakao':
            extra_data = sociallogin.account.extra_data
            properties = extra_data.get('properties', {})
            kakao_account = extra_data.get('kakao_account', {})
            profile = kakao_account.get('profile', {})
            
            # 닉네임 설정 (properties 또는 profile에서)
            nickname = properties.get('nickname') or profile.get('nickname')
            if not user.first_name and nickname:
                user.first_name = nickname
            
            # 카카오 로그인 시 사용자명이 없으면 카카오 ID로 생성
            if not user.username:
                kakao_id = extra_data.get('id')
                if kakao_id:
                    username = f"kakao_{kakao_id}"
                    # 중복 확인
                    if not User.objects.filter(username=username).exists():
                        user.username = username
        
        return user


class CustomAccountAdapter(DefaultAccountAdapter):
    """계정 관련 커스터마이징"""
    
    def is_email_verified(self, request, email_address):
        """이메일 인증 상태 확인"""
        # 소셜 로그인 사용자는 자동으로 인증된 것으로 처리
        if hasattr(request, 'sociallogin'):
            return True
        return super().is_email_verified(request, email_address)

    def save_user(self, request, user, form, commit=True):
        """사용자 저장 시 추가 처리"""
        user = super().save_user(request, user, form, commit=False)
        
        # 추가 커스터마이징이 필요한 경우 여기에 추가
        
        if commit:
            user.save()
        return user 
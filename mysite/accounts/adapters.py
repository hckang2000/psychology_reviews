from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth.models import User


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """소셜 로그인 사용자 정보 커스터마이징"""
    
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
        
        return user


class CustomAccountAdapter(DefaultAccountAdapter):
    """계정 어댑터 커스터마이징"""
    
    def save_user(self, request, user, form, commit=True):
        """사용자 저장 시 추가 처리"""
        user = super().save_user(request, user, form, commit=False)
        
        # 추가 커스터마이징이 필요한 경우 여기에 추가
        
        if commit:
            user.save()
        return user 
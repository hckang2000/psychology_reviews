import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.db import transaction


class Command(BaseCommand):
    help = 'Fix MultipleObjectsReturned error by ensuring only one SocialApp per provider'
    
    def handle(self, *args, **options):
        with transaction.atomic():
            # 1. 모든 SocialApp 삭제 (완전 초기화)
            SocialApp.objects.all().delete()
            self.stdout.write("Deleted all existing SocialApps")
            
            # 2. Site 설정 (기본 Site 사용)
            site, created = Site.objects.get_or_create(
                pk=1,
                defaults={'domain': '127.0.0.1:8000', 'name': 'localhost'}
            )
            if not created:
                site.domain = '127.0.0.1:8000'
                site.name = 'localhost'
                site.save()
            
            # 3. Google SocialApp 생성 (정확히 하나만)
            google_app = SocialApp.objects.create(
                provider='google',
                name='Google',
                client_id=os.getenv('GOOGLE_CLIENT_ID', ''),
                secret=os.getenv('GOOGLE_CLIENT_SECRET', ''),
            )
            google_app.sites.add(site)
            
            # 4. Naver SocialApp 생성 (정확히 하나만)
            naver_app = SocialApp.objects.create(
                provider='naver',
                name='Naver',
                client_id=os.getenv('NAVER_LOGIN_CLIENT_ID', ''),
                secret=os.getenv('NAVER_LOGIN_CLIENT_SECRET', ''),
            )
            naver_app.sites.add(site)
            
            # 5. 결과 확인
            total = SocialApp.objects.count()
            google_count = SocialApp.objects.filter(provider='google').count()
            naver_count = SocialApp.objects.filter(provider='naver').count()
            
            self.stdout.write(f"Created {total} SocialApps:")
            self.stdout.write(f"  - Google: {google_count}")
            self.stdout.write(f"  - Naver: {naver_count}")
            self.stdout.write("MultipleObjectsReturned error should be fixed!") 
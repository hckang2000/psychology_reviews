import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.db import connection


class Command(BaseCommand):
    help = 'Fix MultipleObjectsReturned error by ensuring only one SocialApp per provider'
    
    def handle(self, *args, **options):
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
        
        cursor = connection.cursor()
        
        # 3. Google SocialApp 생성 (직접 SQL 사용)
        try:
            cursor.execute("""
                INSERT INTO socialaccount_socialapp 
                (provider, provider_id, name, client_id, secret, key, settings)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, [
                'google', 'google', 'Google', 
                os.getenv('GOOGLE_CLIENT_ID', ''),
                os.getenv('GOOGLE_CLIENT_SECRET', ''),
                '', '{}'
            ])
            
            # Google app과 site 연결
            google_app = SocialApp.objects.get(provider='google')
            google_app.sites.add(site)
            self.stdout.write("✅ Google SocialApp created successfully")
        except Exception as e:
            self.stdout.write(f"❌ Error creating Google SocialApp: {e}")
        
        # 4. Naver SocialApp 생성 (직접 SQL 사용)
        try:
            cursor.execute("""
                INSERT INTO socialaccount_socialapp 
                (provider, provider_id, name, client_id, secret, key, settings)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, [
                'naver', 'naver', 'Naver',
                os.getenv('NAVER_LOGIN_CLIENT_ID', ''),
                os.getenv('NAVER_LOGIN_CLIENT_SECRET', ''),
                '', '{}'
            ])
            
            # Naver app과 site 연결
            naver_app = SocialApp.objects.get(provider='naver')
            naver_app.sites.add(site)
            self.stdout.write("✅ Naver SocialApp created successfully")
        except Exception as e:
            self.stdout.write(f"❌ Error creating Naver SocialApp: {e}")
        
        # 5. Kakao SocialApp 생성 (직접 SQL 사용)
        try:
            # 카카오 provider가 사용 가능한지 먼저 확인
            from allauth.socialaccount import providers
            available_providers = [p.id for p in providers.registry.get_list()]
            
            if 'kakao' in available_providers:
                cursor.execute("""
                    INSERT INTO socialaccount_socialapp 
                    (provider, provider_id, name, client_id, secret, key, settings)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [
                    'kakao', 'kakao', 'Kakao',
                    os.getenv('KAKAO_REST_API_KEY', ''),
                    os.getenv('KAKAO_CLIENT_SECRET', ''),
                    '', '{}'
                ])
                
                # Kakao app과 site 연결
                kakao_app = SocialApp.objects.get(provider='kakao')
                kakao_app.sites.add(site)
                self.stdout.write("✅ Kakao SocialApp created successfully")
            else:
                self.stdout.write("⚠️ Kakao provider not available in this django-allauth version")
        except Exception as e:
            self.stdout.write(f"❌ Error creating Kakao SocialApp: {e}")
            # 카카오가 실패해도 계속 진행
        
        # 6. 결과 확인
        total = SocialApp.objects.count()
        google_count = SocialApp.objects.filter(provider='google').count()
        naver_count = SocialApp.objects.filter(provider='naver').count()
        kakao_count = SocialApp.objects.filter(provider='kakao').count()
        
        self.stdout.write(f"\n📊 Final Results:")
        self.stdout.write(f"  - Total SocialApps: {total}")
        self.stdout.write(f"  - Google: {google_count}")
        self.stdout.write(f"  - Naver: {naver_count}")
        self.stdout.write(f"  - Kakao: {kakao_count}")
        
        if total >= 2:  # Google + Naver 최소
            self.stdout.write(self.style.SUCCESS("\n🎉 Social login setup completed successfully!"))
        else:
            self.stdout.write(self.style.WARNING("\n⚠️ Some providers failed to set up. Check your environment variables.")) 
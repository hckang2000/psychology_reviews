#!/usr/bin/env python3
"""
Django 환경에서 네이버 Geocoding API 테스트
"""

import os
import sys
import requests

# Django 설정
sys.path.append('mysite')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

try:
    import django
    django.setup()
    from django.conf import settings
    
    print(f"🔍 Django 설정 로드 성공")
    print(f"🔑 NAVER_CLIENT_ID: {settings.NAVER_CLIENT_ID[:10] if settings.NAVER_CLIENT_ID else 'None'}...")
    print(f"🔐 NAVER_CLIENT_SECRET: {settings.NAVER_CLIENT_SECRET[:10] if settings.NAVER_CLIENT_SECRET else 'None'}...")
    
    if not settings.NAVER_CLIENT_ID or not settings.NAVER_CLIENT_SECRET:
        print("❌ API 키가 설정되지 않았습니다.")
        sys.exit(1)
    
    # API 테스트
    headers = {
        'x-ncp-apigw-api-key-id': settings.NAVER_CLIENT_ID,
        'x-ncp-apigw-api-key': settings.NAVER_CLIENT_SECRET,
        'Accept': 'application/json'
    }
    
    test_address = "서울시 강남구 테헤란로 123"
    print(f"📍 테스트 주소: {test_address}")
    
    response = requests.get(
        'https://maps.apigw.ntruss.com/map-geocode/v2/geocode',
        params={'query': test_address},
        headers=headers,
        timeout=10
    )
    
    print(f"📡 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ API 호출 성공!")
        print(f"📄 응답 데이터: {result}")
        
        if result.get('addresses'):
            first_result = result['addresses'][0]
            print(f"🎯 좌표: ({first_result['y']}, {first_result['x']})")
        else:
            print(f"❌ 주소를 찾을 수 없습니다.")
    else:
        print(f"❌ API 호출 실패: {response.text}")
        
except Exception as e:
    print(f"💥 오류 발생: {str(e)}")
    import traceback
    traceback.print_exc() 
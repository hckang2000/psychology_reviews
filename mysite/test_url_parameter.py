#!/usr/bin/env python
import os
import sys
import django

# Django 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from centers.views import index

def test_url_params():
    """URL 파라미터 처리 테스트"""
    factory = RequestFactory()
    
    print("=== URL 파라미터 테스트 ===")
    
    # Test 1: centerId 파라미터
    print("\n1. centerId=415 파라미터 테스트")
    request = factory.get('/centers/?centerId=415')
    request.user = AnonymousUser()
    try:
        response = index(request)
        print(f"✓ 응답 상태: {response.status_code}")
        if 'selected_center_id_json' in response.context_data:
            selected_id = response.context_data['selected_center_id_json']
            print(f"✓ 선택된 센터 ID: {selected_id}")
        else:
            print("❌ selected_center_id_json이 context에 없음")
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # Test 2: center_id 파라미터
    print("\n2. center_id=415 파라미터 테스트")
    request = factory.get('/centers/?center_id=415')
    request.user = AnonymousUser()
    try:
        response = index(request)
        print(f"✓ 응답 상태: {response.status_code}")
        if 'selected_center_id_json' in response.context_data:
            selected_id = response.context_data['selected_center_id_json']
            print(f"✓ 선택된 센터 ID: {selected_id}")
        else:
            print("❌ selected_center_id_json이 context에 없음")
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # Test 3: 파라미터 없음
    print("\n3. 파라미터 없음 테스트")
    request = factory.get('/centers/')
    request.user = AnonymousUser()
    try:
        response = index(request)
        print(f"✓ 응답 상태: {response.status_code}")
        if 'selected_center_id_json' in response.context_data:
            selected_id = response.context_data['selected_center_id_json']
            print(f"✓ 선택된 센터 ID: {selected_id}")
        else:
            print("❌ selected_center_id_json이 context에 없음")
    except Exception as e:
        print(f"❌ 오류: {e}")

if __name__ == '__main__':
    test_url_params() 
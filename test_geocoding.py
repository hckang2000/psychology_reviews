#!/usr/bin/env python3
"""
네이버 Geocoding API 테스트 스크립트
사용법: python test_geocoding.py "서울시 강남구 테헤란로 123"
"""

import os
import sys
import requests
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def test_geocoding(address):
    """주소를 좌표로 변환하는 테스트"""
    
    # 환경변수에서 API 키 가져오기
    client_id = os.getenv('NAVER_CLIENT_ID')
    client_secret = os.getenv('NAVER_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ 환경변수에서 NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET을 찾을 수 없습니다.")
        print("📝 .env 파일을 확인하세요:")
        print("   NAVER_CLIENT_ID=your_client_id")
        print("   NAVER_CLIENT_SECRET=your_client_secret")
        return False
    
    print(f"🔍 테스트 주소: {address}")
    print(f"🔑 Client ID: {client_id[:10]}...")
    print(f"🔐 Client Secret: {client_secret[:10]}...")
    
    # API 요청 헤더
    headers = {
        'x-ncp-apigw-api-key-id': client_id,
        'x-ncp-apigw-api-key': client_secret,
        'Accept': 'application/json'
    }
    
    # API 요청
    try:
        print(f"📡 API 요청 중...")
        response = requests.get(
            'https://maps.apigw.ntruss.com/map-geocode/v2/geocode',
            params={'query': address},
            headers=headers,
            timeout=10
        )
        
        print(f"📋 응답 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API 호출 성공!")
            print(f"📄 응답 데이터: {result}")
            
            if result.get('addresses'):
                first_result = result['addresses'][0]
                latitude = first_result['y']
                longitude = first_result['x']
                road_address = first_result.get('roadAddress', 'N/A')
                jibun_address = first_result.get('jibunAddress', 'N/A')
                
                print(f"🎯 좌표 변환 성공!")
                print(f"   📍 위도: {latitude}")
                print(f"   📍 경도: {longitude}")
                print(f"   🛣️ 도로명주소: {road_address}")
                print(f"   🏠 지번주소: {jibun_address}")
                return True
            else:
                print(f"❌ 주소를 찾을 수 없습니다.")
                print(f"🔍 검색 결과가 없습니다. 주소를 다시 확인해보세요.")
                return False
                
        else:
            print(f"❌ API 호출 실패")
            print(f"📄 응답 내용: {response.text}")
            
            # 오류 코드별 안내
            if response.status_code == 401:
                print("🔐 인증 실패: API 키가 잘못되었거나 만료되었습니다.")
            elif response.status_code == 403:
                print("🚫 접근 권한 없음: NCP 콘솔에서 Geocoding API 서비스를 활성화하세요.")
            elif response.status_code == 429:
                print("📊 API 호출 한도 초과: 일일 허용량을 확인하세요.")
            elif response.status_code == 400:
                print("📝 잘못된 요청: 주소 형식을 확인하세요.")
            
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏰ 타임아웃: API 서버 응답이 늦습니다.")
        return False
    except requests.exceptions.ConnectionError:
        print(f"🌐 연결 오류: 인터넷 연결을 확인하세요.")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")
        return False

def main():
    if len(sys.argv) != 2:
        print("사용법: python test_geocoding.py \"주소\"")
        print("예시: python test_geocoding.py \"서울시 강남구 테헤란로 123\"")
        sys.exit(1)
    
    address = sys.argv[1]
    success = test_geocoding(address)
    
    if success:
        print("\n🎉 테스트 성공! Geocoding API가 정상 작동합니다.")
    else:
        print("\n💥 테스트 실패. 위의 오류 메시지를 확인하세요.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 
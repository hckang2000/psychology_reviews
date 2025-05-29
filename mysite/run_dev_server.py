#!/usr/bin/env python
"""
개발용 서버 실행 스크립트
Chrome HSTS 문제를 피하기 위해 여러 포트를 시도합니다.
"""

import os
import sys
import subprocess

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

def run_server():
    """개발 서버 실행"""
    ports = [8080, 3000, 8001, 8888, 9000]
    
    print("🚀 개발 서버를 시작합니다...")
    print("Chrome HSTS 문제를 피하기 위해 여러 포트를 시도합니다.\n")
    
    for port in ports:
        try:
            print(f"포트 {port}에서 서버 시작 시도...")
            url = f"http://127.0.0.1:{port}"
            
            print(f"✅ 서버가 {url}에서 실행됩니다!")
            print(f"📱 브라우저에서 {url} 접속하세요!")
            print("📋 백업 대시보드: {}/centers/backup/".format(url))
            print("⚙️  관리자 페이지: {}/admin/".format(url))
            print("\n종료하려면 Ctrl+C를 누르세요.\n")
            
            # Django 서버 실행
            subprocess.run([
                sys.executable, 'manage.py', 'runserver', f'127.0.0.1:{port}'
            ])
            break
            
        except KeyboardInterrupt:
            print("\n서버가 종료되었습니다.")
            break
        except Exception as e:
            print(f"포트 {port} 실패: {e}")
            continue

if __name__ == "__main__":
    run_server() 
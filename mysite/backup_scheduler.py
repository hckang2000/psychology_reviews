#!/usr/bin/env python
"""
간단한 백업 스케줄러 (Celery 대안)
사용법: python backup_scheduler.py
"""

import os
import sys
import django
import schedule
import time
from datetime import datetime

# Django 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.core.management import call_command
from io import StringIO

def perform_backup():
    """백업 실행 함수"""
    try:
        print(f"[{datetime.now()}] 자동 백업 시작...")
        
        output = StringIO()
        call_command('backup_data', storage='github', stdout=output)
        
        result = output.getvalue()
        print(f"[{datetime.now()}] 백업 완료: {result}")
        
    except Exception as e:
        print(f"[{datetime.now()}] 백업 실패: {str(e)}")

def main():
    """스케줄러 메인 함수"""
    print("백업 스케줄러 시작...")
    print("매주 일요일 14:00에 자동 백업 실행")
    
    # 매주 일요일 14:00에 백업 실행
    schedule.every().sunday.at("14:00").do(perform_backup)
    
    # 테스트용: 1분마다 실행 (운영시에는 제거)
    # schedule.every(1).minutes.do(perform_backup)
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 체크
    except KeyboardInterrupt:
        print("\n백업 스케줄러 종료")

if __name__ == "__main__":
    main() 
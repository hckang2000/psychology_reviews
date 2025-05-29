@echo off
REM 백업 스케줄러 실행 (Celery 대안)
cd /d "C:\Users\USER\psychology_reviews\mysite"
call ..\venv\Scripts\activate.bat

echo 백업 스케줄러 시작...
echo 매주 일요일 14:00에 자동 백업 실행됩니다.
echo 종료하려면 Ctrl+C를 누르세요.

python backup_scheduler.py
pause 
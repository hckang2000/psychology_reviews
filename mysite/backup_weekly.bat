@echo off
REM 자동 백업 스케줄러 실행
REM 매주 일요일 14:00에 GitHub Releases로 백업
cd /d "C:\Users\USER\psychology_reviews\mysite"
call ..\venv\Scripts\activate.bat

echo ============================================
echo    마인드스캐너 백업 스케줄러 시작
echo ============================================
echo 매주 일요일 14:00에 자동 백업이 실행됩니다.
echo 종료하려면 Ctrl+C를 누르세요.
echo.

python backup_scheduler.py
pause 
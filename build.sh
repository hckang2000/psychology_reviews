#!/usr/bin/env bash
# exit on error
set -o errexit

# Install python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p mysite/staticfiles
mkdir -p mysite/logs

cd mysite
# 정적 파일 수집
python manage.py collectstatic --no-input
# 데이터베이스 마이그레이션
python manage.py migrate 
# Superuser 자동 생성 (환경변수가 설정된 경우에만)
if [ ! -z "$DJANGO_SUPERUSER_USERNAME" ]; then
    python manage.py create_superuser
fi 
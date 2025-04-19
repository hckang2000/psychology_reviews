#!/usr/bin/env bash
# exit on error
set -o errexit

# Install python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create staticfiles directory if it doesn't exist
mkdir -p mysite/staticfiles

cd mysite
# 정적 파일 수집
python manage.py collectstatic --no-input
# 데이터베이스 마이그레이션
python manage.py migrate 
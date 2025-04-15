#!/bin/bash
# exit on error
set -o errexit

# Python 및 pip 업그레이드
python -m pip install --upgrade pip

# 의존성 설치
pip install -r requirements.txt

# 정적 파일 수집 및 데이터베이스 마이그레이션
cd mysite
python manage.py collectstatic --no-input
python manage.py migrate 
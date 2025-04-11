# MindScanner - 심리상담센터 리뷰 플랫폼

## 프로젝트 소개
MindScanner는 사용자들이 심리상담센터를 쉽게 찾고 리뷰를 공유할 수 있는 플랫폼입니다. 네이버 지도 API를 활용하여 상담센터의 위치를 시각적으로 보여주며, 사용자들은 각 센터에 대한 리뷰를 작성하고 공유할 수 있습니다.

## 주요 기능
- 🗺️ **지도 기반 상담센터 검색**
  - 네이버 지도 API를 활용한 시각적 위치 표시
  - 상담센터 위치 마커 표시
  - 클릭 시 상세 정보 확인

- 📝 **상담센터 정보 제공**
  - 상담센터 기본 정보 (이름, 주소, 연락처, 웹사이트)
  - 이미지 갤러리
  - 운영 시간 정보

- ✍️ **리뷰 시스템**
  - 사용자 리뷰 작성
  - 리뷰 목록 조회
  - 리뷰 평점 시스템

- 👤 **사용자 관리**
  - 회원가입/로그인
  - 사용자별 리뷰 관리

## 기술 스택
- **Backend**: Django
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite (개발 환경)
- **External API**: 네이버 지도 API
- **이미지 처리**: Pillow

## 설치 및 실행 방법

1. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

2. 필요한 패키지 설치
```bash
pip install django pillow
```

3. 데이터베이스 마이그레이션
```bash
python manage.py makemigrations
python manage.py migrate
```

4. 서버 실행
```bash
python manage.py runserver
```

5. 웹 브라우저에서 접속
```
http://127.0.0.1:8000
```

## 환경 설정
1. 네이버 지도 API 클라이언트 ID 설정
   - `index.html`의 네이버 지도 API 스크립트 태그에 클라이언트 ID 입력

2. 정적 파일 설정
   - `settings.py`에서 STATICFILES_DIRS 설정 확인
   - static 폴더 생성 및 정적 파일 배치

## 프로젝트 구조
```
mysite/
├── centers/
│   ├── templates/
│   │   └── index.html
│   ├── static/
│   │   ├── centers/
│   │   │   ├── styles.css
│   │   │   └── map.js
│   │   └── ...
│   └── ...
├── manage.py
└── ...
```

## 기여 방법
1. 이슈 생성
2. 브랜치 생성
3. 코드 작성
4. Pull Request 요청

## 라이선스
이 프로젝트는 MIT 라이선스를 따릅니다. 
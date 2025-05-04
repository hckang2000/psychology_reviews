# MindScanner - 심리상담센터 리뷰 플랫폼

## 프로젝트 소개
MindScanner는 사용자들이 심리상담센터를 쉽게 찾고 리뷰를 공유할 수 있는 종합적인 플랫폼입니다. 네이버 지도 API를 활용하여 상담센터의 위치를 시각적으로 보여주며, 사용자들은 각 센터에 대한 리뷰를 작성하고 공유할 수 있습니다. 또한 커뮤니티 기능을 통해 사용자들 간의 소통을 지원합니다.

## 주요 기능
- 🗺️ **지도 기반 상담센터 검색**
  - 네이버 지도 API를 활용한 시각적 위치 표시
  - 상담센터 위치 마커 표시
  - 클릭 시 상세 정보 확인
  - 상담센터 사진 갤러리

- 📝 **상담센터 정보 제공**
  - 상담센터 기본 정보 (이름, 주소, 연락처, 웹사이트)
  - 상담사 정보 (이름, 전문분야, 경력, 사진)
  - 운영 시간 정보
  - 상담센터 소개 및 특징

- ✍️ **리뷰 시스템**
  - 사용자 리뷰 작성 및 관리
  - 리뷰 평점 시스템 (1-5점)
  - 외부 리뷰 통합 (블로그 등)
  - 리뷰 검색 및 필터링

- 💬 **커뮤니티 기능**
  - 자유게시판
  - 익명게시판
  - 댓글 시스템
  - 게시글 검색

- 👤 **사용자 관리**
  - 회원가입/로그인
  - 사용자별 리뷰 및 게시글 관리
  - 프로필 관리
  - 비밀번호 변경

## 기술 스택
- **Backend**: Django 4.2
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Database**: SQLite (개발 환경)
- **External API**: 네이버 지도 API
- **이미지 처리**: Pillow
- **배포**: Render
- **버전 관리**: Git

## 프로젝트 구조
```
mysite/
├── centers/                 # 상담센터 관련 앱
│   ├── models.py           # 상담센터, 상담사, 리뷰 모델
│   ├── views.py            # 상담센터 관련 뷰
│   ├── templates/          # 상담센터 관련 템플릿
│   └── static/             # 상담센터 관련 정적 파일
├── boards/                  # 게시판 관련 앱
│   ├── models.py           # 게시글, 댓글 모델
│   ├── views.py            # 게시판 관련 뷰
│   └── templates/          # 게시판 관련 템플릿
├── accounts/               # 사용자 인증 관련 앱
│   ├── models.py          # 사용자 모델
│   ├── views.py           # 인증 관련 뷰
│   └── templates/         # 인증 관련 템플릿
├── mysite/                 # 프로젝트 설정
│   ├── settings.py        # 프로젝트 설정
│   ├── urls.py            # URL 설정
│   └── wsgi.py            # WSGI 설정
├── staticfiles/           # 정적 파일 모음
├── media/                 # 업로드된 미디어 파일
├── requirements.txt       # 의존성 패키지 목록
├── render.yaml            # Render 배포 설정
├── Procfile              # 프로세스 설정
└── manage.py             # Django 관리 명령어
```

## 설치 및 실행 방법

1. 가상환경 생성 및 활성화
```bash
python -m venv .venv
.\venv\Scripts\activate   # Windows
```

2. 필요한 패키지 설치
```bash
pip install -r requirements.txt
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
   - `settings.py`에 NAVER_MAP_CLIENT_ID 설정 추가

2. 정적 파일 설정
   - `settings.py`에서 STATICFILES_DIRS 설정 확인
   - static 폴더 생성 및 정적 파일 배치

3. 미디어 파일 설정
   - `settings.py`에서 MEDIA_ROOT 설정 확인
   - media 폴더 생성

## 배포 정보
- Render를 통한 자동 배포
- `render.yaml` 설정 파일 사용
- `Procfile`을 통한 웹 서버 실행 설정
- `build.sh` 스크립트를 통한 빌드 자동화

## 기여 방법
1. 이슈 생성
2. 브랜치 생성
3. 코드 작성
4. Pull Request 요청

## 라이선스
이 프로젝트는 MIT 라이선스를 따릅니다. 
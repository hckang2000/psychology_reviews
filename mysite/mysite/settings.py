import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-your-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
# Render 환경에서는 자동으로 DEBUG=False, 로컬에서는 DEBUG=True
DEBUG = not bool(os.getenv('RENDER'))  # RENDER 환경변수가 있으면 False, 없으면 True

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'mindscanner.onrender.com',  # 도메인 수정
    '.onrender.com'
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third party apps
    'accounts',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'django_extensions',  # URL 디버깅을 위해 추가
    
    # Local apps
    'centers',
    'boards',
    'crispy_forms',
    'crispy_bootstrap5',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'accounts/templates'),
            os.path.join(BASE_DIR, 'centers/templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mysite.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
    os.path.join(BASE_DIR, 'centers/static'),
    os.path.join(BASE_DIR, 'boards/static'),
]

# WhiteNoise 설정
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

# Allauth settings
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 5
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = '/'
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = 'account_login'
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[마인드스캐너] '
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http' if DEBUG else 'https'
ACCOUNT_FORMS = {
    'login': 'accounts.forms.CustomLoginForm',
    'signup': 'accounts.forms.CustomSignupForm',
}

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Naver Maps API
NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')

# Login and logout redirects
LOGIN_REDIRECT_URL = 'centers:index'
LOGIN_URL = 'accounts:account_login'
LOGOUT_REDIRECT_URL = 'centers:index'

# Security settings - 운영환경(Render)에서만 HTTPS 강제
if not DEBUG:  # 운영환경 (RENDER=True)
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:  # 개발환경 (로컬)
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# CSRF settings - 환경별 자동 구분
if DEBUG:  # 개발환경 (로컬)
    CSRF_TRUSTED_ORIGINS = [
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ]
else:  # 운영환경 (Render)
    CSRF_TRUSTED_ORIGINS = [
        'https://mindscanner.onrender.com'
    ]

# ============================================
# 백업 시스템 설정
# ============================================

# 백업 시스템 설정
BACKUP_DEFAULT_STORAGE = os.getenv('BACKUP_DEFAULT_STORAGE', 'github')  # GitHub를 기본으로 변경
BACKUP_COMPRESS_DEFAULT = os.getenv('BACKUP_COMPRESS_DEFAULT', 'True').lower() == 'true'
BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))

# GitHub 백업 설정 (추가)
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_BACKUP_REPO = os.getenv('GITHUB_BACKUP_REPO', 'hckang2000/mindscanner-backup')

# AWS S3 백업 설정 (선택사항)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_BACKUP_BUCKET_NAME = os.getenv('AWS_BACKUP_BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'ap-northeast-2')

# Google Drive 백업 설정 (선택사항)
GOOGLE_DRIVE_WEBHOOK_URL = os.getenv('GOOGLE_DRIVE_WEBHOOK_URL')

# 백업할 모델 목록 (centers 앱)
BACKUP_DEFAULT_MODELS = [
    'Center',
    'InternalReview', 
    'ExternalReview',
    'Therapist'
]

# 로깅 설정 (백업 관련)
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)  # logs 디렉토리 자동 생성

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'centers.tasks': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# 운영 환경이 아닌 경우에만 파일 로깅 추가
if DEBUG or not os.getenv('RENDER'):
    LOGGING['handlers']['file'] = {
        'level': 'INFO',
        'class': 'logging.FileHandler',
        'filename': os.path.join(LOG_DIR, 'backup.log'),
        'formatter': 'verbose',
    }
    # 파일 핸들러를 로거에 추가
    for logger_name in ['centers.tasks', 'django']:
        if logger_name in LOGGING['loggers']:
            LOGGING['loggers'][logger_name]['handlers'].append('file')

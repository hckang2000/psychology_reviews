import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api

# .env 파일 로드
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-your-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
# Render 환경에서는 자동으로 DEBUG=False, 로컬에서는 DEBUG=True
DEBUG = not bool(os.getenv('RENDER'))  # RENDER 환경변수가 있으면 False, 없으면 True

# ALLOWED_HOSTS를 환경변수에서 읽어오기
ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if host.strip()]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Cloudinary apps (django.contrib.staticfiles 이후에 위치)
    'cloudinary_storage',
    'cloudinary',
    
    # Third party apps
    'accounts',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.naver',
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
    # 'allauth.account.middleware.AccountMiddleware',  # 0.54.0에서는 존재하지 않음
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
            'debug': DEBUG,  # 템플릿 디버깅 활성화
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
# 프로덕션 환경(Render)에서는 PostgreSQL, 로컬에서는 SQLite 사용
if os.getenv('RENDER'):
    # Render 프로덕션 환경: PostgreSQL 사용
    DATABASES = {
        'default': dj_database_url.config(
            # Render에서 자동으로 설정되는 DATABASE_URL 환경변수 사용
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # 로컬 개발 환경: SQLite 사용
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'OPTIONS': {
                'timeout': 20,
            }
        }
    }

# SQLite Foreign Key 지원 활성화 (로컬 환경에서만)
if not os.getenv('RENDER') and 'sqlite' in DATABASES['default']['ENGINE']:
    DATABASES['default']['OPTIONS'] = {
        'timeout': 20,
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
    os.path.join(BASE_DIR.parent, 'static'),  # 프로젝트 루트의 static 디렉토리
    os.path.join(BASE_DIR, 'centers/static'),
    os.path.join(BASE_DIR, 'boards/static'),
]

# STATICFILES_FINDERS 추가 - 정적 파일 수집 개선
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# WhiteNoise 설정 - 운영환경에서 정적 파일 오류 방지
if DEBUG:
    # 개발환경: 기본 설정
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    # 운영환경: 매니페스트 없는 압축 스토리지 사용 (안정성 우선)
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Cloudinary 설정
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET'),
}

# Cloudinary 초기화
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

# 운영환경에서는 Cloudinary, 개발환경에서는 로컬 저장소 사용
if os.getenv('RENDER'):
    # 운영환경: Cloudinary 사용
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
else:
    # 개발환경: 로컬 미디어 저장소 사용
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

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
# Rate limiting 설정 제거 (django-allauth 0.54.0 호환)
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

# Custom adapters for social login
ACCOUNT_ADAPTER = 'accounts.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.CustomSocialAccountAdapter'

# Social account settings - 중간 확인 페이지 건너뛰기
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True

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

# Session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_COOKIE_NAME = 'sessionid'
SESSION_SAVE_EVERY_REQUEST = True  # 매 요청마다 세션 저장
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Cache settings - 환경별 분리
if os.getenv('RENDER'):
    # Render 프로덕션 환경: Database cache 사용 (PostgreSQL)
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'django_cache_table',
            'TIMEOUT': 600,  # 10 minutes
            'OPTIONS': {
                'MAX_ENTRIES': 5000,
                'CULL_FREQUENCY': 3,
            }
        }
    }
else:
    # 로컬 개발 환경: LocMemCache 사용
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
            'TIMEOUT': 600,  # 10 minutes
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
            }
        }
    }

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
    'Review', 
    'ExternalReview',
    'Therapist',
    'CenterImage',
    'ReviewComment'
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

# Social Login Settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    },
    'naver': {
        'APP': {
            'client_id': os.getenv('NAVER_LOGIN_CLIENT_ID'),
            'secret': os.getenv('NAVER_LOGIN_CLIENT_SECRET'),
            'key': ''
        }
    }
}

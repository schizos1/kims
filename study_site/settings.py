"""
Django settings for study_site project.
경로: ~/study_site/study_site/settings.py
- 한글화, 서울 타임존, PostgreSQL 연결 (studyuser)
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-임시값'

DEBUG = True

ALLOWED_HOSTS = ['192.168.31.199']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 사용자 앱
    'users.apps.UsersConfig',
    'quiz',
    'trophies',
    'core',
    'attendance',
    'store',
    'minigame',
    'corsheaders',
    'pdf_importer',    # PDF 임포트 기능
]

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'attendance.middleware.AttendanceMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'study_site.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'users.context_processors.user_profile_for_base',
            ],
        },
    },
]
# 허용할 출처 목록
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://192.168.31.199:3001', # Socket.IO 서버 주소
]
# Channels (ASGI) 세팅
#ASGI_APPLICATION = 'study_site.asgi.application'

#CHANNEL_LAYERS = {
#    "default": {
#        "BACKEND": "channels.layers.InMemoryChannelLayer",
#        # 운영 환경에서는 channels_redis로 변경 권장!
#        # "BACKEND": "channels_redis.core.RedisChannelLayer",
#        # "CONFIG": {"hosts": [("127.0.0.1", 6379)],},
#    }
#}

WSGI_APPLICATION = 'study_site.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'study_db',
        'USER': 'studyuser',
        'PASSWORD': 'secure_password_2025',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_ROOT = str(BASE_DIR / 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR / "users/static",
    BASE_DIR / "minigame/static",
]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 로그 설정 (개발용)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler',},
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}

# 로그아웃 후 리디렉트 경로
LOGOUT_REDIRECT_URL = '/'

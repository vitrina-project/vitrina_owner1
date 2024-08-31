import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

if (BASE_DIR.parent / 'infra' / 'local' / '.env').exists():
    load_dotenv(BASE_DIR.parent / 'infra' / 'local' / '.env')


def get_required_env(name, default=None):
    param = os.getenv(name, default)
    if param is None:
        raise AttributeError(f"Missing environment variable {name}")
    return param


SECRET_KEY = get_required_env('DJANGO_SECRET_KEY')

DEBUG = get_required_env('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = get_required_env('ALLOWED_HOSTS', '*').split(',')

CORS_ALLOW_ALL_ORIGINS = True
# CSRF_TRUSTED_ORIGINS = [
#
# ]

INSTALLED_APPS = [
    'jazzmin',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',
    'rest_framework',
    'djoser',
    'drf_spectacular',

    'users',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'core.middleware.BaseAPIResponseMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

DEBUG_APPS = [
    'debug_toolbar',
]

DEBUG_MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

if DEBUG:
    INSTALLED_APPS.extend(DEBUG_APPS)
    MIDDLEWARE.extend(DEBUG_MIDDLEWARE)


def show_toolbar(request):
    return DEBUG


DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': show_toolbar,
}

ROOT_URLCONF = 'vitrina.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

WSGI_APPLICATION = 'virtina.wsgi.application'

DB_HOST = get_required_env('POSTGRES_HOST', 'localhost')

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": get_required_env('POSTGRES_DB'),
        "USER": get_required_env('POSTGRES_USER'),
        "PASSWORD": get_required_env('POSTGRES_PASSWORD'),
        "HOST": DB_HOST,
        "PORT": get_required_env('POSTGRES_PORT', 5432),
    }
}

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

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'
STATICFILES_DIRS = [
    BASE_DIR / 'staticfiles'
]

MEDIA_URL = 'media/'

MEDIA_ROOT = BASE_DIR / 'media/'

AUTH_USER_MODEL = 'users.User'
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.AllowAllUsersModelBackend']

SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('JWT',),
    'ACCESS_TOKEN_LIFETIME': timedelta(days=30),
    "TOKEN_OBTAIN_SERIALIZER": "core.jwt.TokenObtainPairSerializer",
}


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

DJOSER = {
    'LOGIN_FIELD': 'phone',
    'PERMISSIONS': {
        'user_list': ['rest_framework.permissions.IsAdminUser'],
    },
    'SERIALIZERS': {
        'current_user': 'users.serializers.UserSerializer',
        'password_reset_confirm': 'users.serializers.ConfirmCodeSerializer'
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(asctime)s [%(levelname)s]: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },
    },
    'loggers': {
        '': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': True
        }
    },
}

REDIS_PASSWORD = get_required_env('REDIS_PASSWORD')
REDIS_HOST = get_required_env('REDIS_HOST')
REDIS_PORT = get_required_env('REDIS_PORT')
REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"

# SMSC
SMSC_LOGIN = get_required_env('SMSC_LOGIN')
SMSC_PASSWORD = get_required_env('SMSC_PASSWORD')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

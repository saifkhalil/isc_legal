"""
Django settings for isc_legal project.

Generated by 'django-admin startproject' using Django 3.1.14.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path
import os
from django.utils.translation import gettext_lazy as _
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'cw#703dwo68e^5nl^t=i*7s4pr3aas6ztgmak!jua1w!^c&^ah'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'rest_framework_swagger',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_word_filter',

    'djoser',
    'phonenumber_field',
    'import_export',
    'crispy_bootstrap5',
    'easy_thumbnails',
    'rosetta',
    'ckeditor',
    'widget_tweaks',
    'drf_yasg',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'rest_framework_simplejwt',
    'django_filters',
    'corsheaders',
    'accounts',
    'core',
    'cases',
    'activities',
    'tabular_permissions',
    'crispy_forms',
    'slick_reporting',
    'logentry_admin',
    'celery',
    'django_celery_beat',   
    'django_celery_results',
    # 'rest_framework_tracking',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware', 
    # 'django.middleware.cache.UpdateCacheMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.cache.FetchFromCacheMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.current_user.RequestMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': os.environ.get('MYSQL_DATABASE', 'isc_legal'),
#         'USER': os.environ.get('MYSQL_USER', 'isc_legal'),
#         'PASSWORD': os.environ.get('MYSQL_PASSWORD', 'Isc@L3gal'),
#         'HOST': os.environ.get('MYSQL_DATABASE_HOST', 'localhost'),
#         'PORT': os.environ.get('MYSQL_DATABASE_PORT', 3306),
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('MYSQL_DATABASE', 'isc_legal'),
        'USER': os.environ.get('MYSQL_USER', 'isc_legal'),
        'PASSWORD': os.environ.get('MYSQL_PASSWORD', 'Isc@L3gal'),
        'HOST': os.environ.get('MYSQL_DATABASE_HOST', 'localhost'),
        'PORT': os.environ.get('MYSQL_DATABASE_PORT', 5432),
    }
}
# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en'

TIME_ZONE = 'Asia/Baghdad'

USE_I18N = True

USE_L10N = True

USE_TZ = True

SITE_ID = 1

LANGUAGES = (
    ('en', _('English')),
    ('ar', _('Arabic')),
)

LOCALE_PATHS = [
    BASE_DIR / 'locale/',
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]


AUTH_USER_MODEL = 'accounts.User'

LOGIN_REDIRECT_URL = 'home'
LOGIN_URL = 'login'

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissions',
        
    ],
    # 'DEFAULT_CONTENT_NEGOTIATION_CLASS': 'core.negotiation.IgnoreClientContentNegotiation',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,

    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'ISC Legal App',
    'DESCRIPTION': 'ISC Legal App',
    'VERSION': '0.3',
    'SERVE_INCLUDE_SCHEMA': False,
    'CONTACT': {"name":"Saif AlKhateeb","email":"saif.ibrahim@qi.iq"},
}

SIMPLE_JWT = {
    'BLACKLIST_AFTER_ROTATION': False,
}


PARLER_LANGUAGES = {
    None: (
        {'code': 'en',},
        {'code': 'ar',},
    ),
    'default': {
        'fallback': 'en',             # defaults to PARLER_DEFAULT_LANGUAGE_CODE
        'hide_untranslated': False,   # the default; let .active_translations() return fallbacks too.
    }
}

PARLER_DEFAULT_LANGUAGE_CODE = 'en'


# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': 'redis://' + os.environ.get('REDIS_HOST', 'localhost') + ':6379',
#     }
# }


# CACHE_MIDDLEWARE_ALIAS = 'default'  # The cache alias to use for storage and 'default' is **local-memory cache**.
# CACHE_MIDDLEWARE_SECONDS = 3600
# CACHE_MIDDLEWARE_KEY_PREFIX = ''    # This is used when cache is shared across multiple sites that
DATA_UPLOAD_MAX_NUMBER_FIELDS = 99999


CORS_ALLOW_ALL_ORIGINS = True # If this is used then `CORS_ALLOWED_ORIGINS` will not have any effect
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'https://localhost:3000',
] # If this is used, then not need to use `CORS_ALLOW_ALL_ORIGINS = True`
CORS_ALLOWED_ORIGIN_REGEXES = [
    'http://localhost:3000',
    'https://localhost:3000',
]


JAZZMIN_SETTINGS = {
    "show_ui_builder" : True
}
JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "dark_mode_theme": "darkly",
}


TABULAR_PERMISSIONS_CONFIG = {
    'template': 'tabular_permissions/admin/tabular_permissions.html',
    'exclude': {
        'override': False,
        'apps': [],
        'models': [],
        'function':'tabular_permissions.helpers.dummy_permissions_exclude'
    },
    'auto_implement': True,
    'use_for_concrete': False,
    'custom_permission_translation': 'tabular_permissions.helpers.custom_permissions_translator',
    'apps_customization_func': 'tabular_permissions.helpers.apps_customization_func',
    'custom_permissions_customization_func': 'tabular_permissions.helpers.custom_permissions_customization_func',
}

CRISPY_TEMPLATE_PACK = 'bootstrap4'


#### SMTP CONFIGURATION ####

EMAIL_HOST = 'smtp.office365.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = 'legal.app@qi.iq'
EMAIL_HOST_PASSWORD = 'Bog91158'
DEFAULT_FROM_EMAIL = 'Legal Application <legal.app@qi.iq>'


CELERY_TIMEZONE = 'Asia/Baghdad'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60

CELERY_RESULT_BACKEND = 'django-db'
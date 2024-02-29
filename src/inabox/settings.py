"""
Django settings for inabox project.

Generated by 'django-admin startproject' using Django 4.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os

from django_auth_ldap.config import LDAPSearch
import ldap

from .bootstrap5 import BOOTSTRAP5

ADMINS = [("karasu", "inabox@ies-sabadell.cat")]

#AUTH_USER_MODEL = "app.InaboxUser"

AUTH_LDAP_BIND_DN = ""
AUTH_LDAP_BIND_PASSWORD = ""
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "ou=users,dc=inabox,dc=ies-sabadell,dc=cat",
    ldap.SCOPE_SUBTREE,
    "(uid=%(user)s)"
)
AUTH_LDAP_START_TLS = False

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY_FILE=os.environ.get('DJANGO_SECRET_KEY_FILE', None)
if SECRET_KEY_FILE:
    with open(SECRET_KEY_FILE, 'rt', encoding='utf-8') as skf:
        SECRET_KEY=skf.readline()
else:
    SECRET_KEY = os.environ.get(
        'DJANGO_SECRET_KEY',
        'django-insecure-$&50skc3lh+e7+ukdex*5u07o_o%_x93u&xw6#%r5w-60#iw@n')

# SECURITY WARNING: don't run with debug turned on in production!
# if DEBUG var does not exist, we assume we're running in debug mode
DEBUG = os.environ.get('DJANGO_DEBUG', "True")

if DEBUG != "True":
    DEBUG = None

if DEBUG:
    print("DJANGO is running in DEBUG mode")
else:
    print("DJANGO is running in PRODUCTION mode")

if DEBUG:
    ALLOWED_HOSTS = []
else:
    ALLOWED_HOSTS = [
        '.ies-sabadell.cat',
        'localhost',
        '127.0.0.1',
        '[::1]' ]
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Application definition

INSTALLED_APPS = [
#    'compressor',
    'daphne',
    #'debug_toolbar',
    'admin_interface',
    'colorfield',
    'django_bootstrap5',
    'django_celery_beat',
    'django_celery_results',
    'celery_progress',
    'app.apps.InaboxConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    #'django.middleware.cache.UpdateCacheMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    #'django.middleware.cache.FetchFromCacheMiddleware',

]

AUTHENTICATION_BACKENDS = [
    "django_auth_ldap.backend.LDAPBackend",
    "django.contrib.auth.backends.ModelBackend",
]

ROOT_URLCONF = 'inabox.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ BASE_DIR / 'inabox/templates' ],
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

WSGI_APPLICATION = 'inabox.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

if DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            'NAME': os.path.join(BASE_DIR , 'db.sqlite3'),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "postgres",
            "USER": "postgres",
            "PASSWORD": "development",
            "HOST": "postgres.inabox.ies-sabadell.cat",
            "PORT": "5432",
        }
    }

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

#LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'ca'
LANGUAGES = (
 ('ca', 'Catalan'),
 ('en', 'English'),
)

TIME_ZONE = 'Europe/Rome'

USE_I18N = True
USE_TZ = True

################################################
########## Static files configuration ##########
################################################
# See <https://docs.djangoproject.com/en/3.2/howto/static-files/>.

# Change this to somewhere more permanent, especially if you are using a
# webserver to serve the static files. This is the directory where all the
# static files DMOJ uses will be collected to.
# You must configure your webserver to serve this directory as /static/ in production.

STATIC_ROOT = '/tmp/static'

# URL to access static files.
if DEBUG:
    STATIC_URL = '/tmp/static/'
else:
    STATIC_URL = 'https://static.inabox.ies-sabadell.cat/static/'

# Uncomment to use hashed filenames with the cache framework.
#STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

if DEBUG:
    MEDIA_URL = '/media/'
else:
    MEDIA_URL = 'https://static.inabox.ies-sabadell.cat/media/'

#STATICFILES_FINDERS = [
#    "compressor.finders.CompressorFinder",
#]

#COMPRESS_PRECOMPILERS = (
#    ('text/x-scss', 'django_libsass.SassCompiler'),
#)

#STATICFILES_FINDERS = [
#    "django.contrib.staticfiles.finders.FileSystemFinder",
#    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
#]

# The Debug Toolbar is shown only if your IP address is listed in Django’s INTERNAL_IPS setting.
# This means that for local development, you must add "127.0.0.1" to INTERNAL_IPS.

INTERNAL_IPS = [
    '127.0.0.1'
]

# Daphne
ASGI_APPLICATION = "inabox.asgi.application"

# Channels
if DEBUG:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [("127.0.0.1", 6379)],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis.inabox.ies-sabadell.cat", 6379)],
        },
    },
}

# Login admin options
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/accounts/login/'
LOGOUT_REDIRECT_URL = 'loggedout'

# Celery Configuration Options
CELERY_TIMEZONE = 'Europe/Rome'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'

if DEBUG:
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
else:
    CELERY_BROKER_URL = 'redis://redis.inabox.ies-sabadell.cat:6379/0'

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

if DEBUG is None:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": "redis://redis.inabox.ies-sabadell.cat:6379",
        }
    }


SECRET_KEY_FILE=os.environ.get('DJANGO_SECRET_KEY_FILE', None)
if SECRET_KEY_FILE:
    with open(SECRET_KEY_FILE, 'rt', encoding='utf-8') as skf:
        SECRET_KEY=skf.readline()
else:
    SECRET_KEY = os.environ.get(
        'DJANGO_SECRET_KEY',
        'django-insecure-$&50skc3lh+e7+ukdex*5u07o_o%_x93u&xw6#%r5w-60#iw@n')

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = "smtp.gmail.com"
EMAIL_HOST_USER = "mailgoeshere"
EMAIL_HOST_PASSWORD = "your email password"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = "Inabox mailgoeshere"

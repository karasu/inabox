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
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY','django-insecure-$&50skc3lh+e7+ukdex*5u07o_o%_x93u&xw6#%r5w-60#iw@n')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', '') != 'False'
print(f"DJANGO_DEBUG={DEBUG}")

if DEBUG:
    ALLOWED_HOSTS = []
else:
    ALLOWED_HOSTS = [ 'inabox1.ies-sabadell.cat' ]
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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": "development",
        "HOST": "127.0.0.1",
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
#STATIC_ROOT = '/tmp/static'

# URL to access static files.
STATIC_URL = '/static/'

# Uncomment to use hashed filenames with the cache framework.
#STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# This needs to be changed in production
MEDIA_ROOT = '/tmp'

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
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

# Login admin options
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = '/accounts/login/'
LOGOUT_REDIRECT_URL = "loggedout"

# Celery Configuration Options
CELERY_TIMEZONE = "Europe/Rome"
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
# Use rabbitmq
CELERY_BROKER_URL = 'amqp://guest:guest@localhost'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

#CACHES = {
#    "default": {
#        "BACKEND": "django.core.cache.backends.redis.RedisCache",
#        "LOCATION": "redis://127.0.0.1:6379",
#    }
#}

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

BOOL_STR = {
    "True": ['true', '1', 'y', 'yes'],
    "False": ['false', '0', 'n', 'no']}

def is_bool(mystr):
    """ check if string can be converted to bool """
    mystr = mystr.lower()
    if mystr in BOOL_STR['True'] or mystr in BOOL_STR['False']:
        return True
    return False 

def to_bool(mystr):
    """ convert string to bool """
    mystr = mystr.lower()
    if mystr in BOOL_STR['True']:
        return True
    return False

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
# if DEBUG var does not exist, we assume we're running in debug mode
DEBUG = os.environ.get('DJANGO_DEBUG', 'True')

if not to_bool(DEBUG):
    DEBUG = None

# load secret settings
SECRETS = {}
SECRETS_PATH = os.path.join(BASE_DIR.parent, 'secrets.txt')
print("loading secrets from", SECRETS_PATH)
if os.path.exists(SECRETS_PATH):
    with open(SECRETS_PATH, 'rt', encoding='utf-8') as sf:
        line = sf.readline()
        while line:
            if not line.startswith('#') and '=' in line:
                line = line.split('=')
                try:
                    name = line[0].strip()
                    value = line[1].strip()
                    if value[0] == "'":
                        value = value.strip("'")
                    elif value[0] == '"':
                        value = value.strip('"')
                    elif is_bool(value):
                        value = to_bool(value)
                    else:
                        value = int(value)
                    SECRETS[name] = value
                except (IndexError, KeyError, TypeError) as exc:
                    print(exc)
            line = sf.readline()

#print(SECRETS)

ADMINS = [(
    SECRETS.get("ADMIN_USERNAME", "admin"),
    SECRETS.get("ADMIN_EMAIL", "admin@admin.com"))]

# LDAP
AUTH_LDAP_SERVER_URI = "ldap://ldap.inabox.ies-sabadell.cat"
AUTH_LDAP_BIND_DN = ""
AUTH_LDAP_BIND_PASSWORD = ""
AUTH_LDAP_USER_DN_TEMPLATE = "uid=%(user)s,ou=users,dc=inabox,dc=ies-sabadell,dc=cat"
#AUTH_LDAP_USER_SEARCH = LDAPSearch(
#    "ou=users,dc=inabox,dc=ies-sabadell,dc=cat",
#    ldap.SCOPE_SUBTREE,
#    "(uid=%(user)s)"
#)
AUTH_LDAP_START_TLS = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SECRETS.get(
    "SECRET_KEY",
    'django-insecure-$&50skc3lh+e7+ukdex*5u07o_o%_x93u&xw6#%r5w-60#iw@n')


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
        '[::1]']
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
    'django_minify_html',
]

MIDDLEWARE = [
    #'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django_minify_html.middleware.MinifyHtmlMiddleware',
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

TEMPLATES = [{
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
        },
        'ldap': {
            'ENGINE': 'ldapdb.backends.ldap',
            'NAME': 'ldap://ldap.inabox.ies-sabadell.cat/',
            'USER': 'cn=admin,dc=inabox,dc=ies-sabadell,dc=cat',
            'PASSWORD': SECRETS.get("LDAP_DB_PASSWORD", "development"),
        },
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "postgres",
            "USER": "postgres",
            "PASSWORD": SECRETS.get("DB_PASSWORD", "development"),
            "HOST": "postgres.inabox.ies-sabadell.cat",
            "PORT": "5432",
        },
        'ldap': {
            'ENGINE': 'ldapdb.backends.ldap',
            'NAME': 'ldap://ldap.inabox.ies-sabadell.cat/',
            'USER': 'cn=admin,dc=inabox,dc=ies-sabadell,dc=cat',
            'PASSWORD': SECRETS.get("LDAP_DB_PASSWORD", "development"),
        },
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

# URL to access static files.
if DEBUG:
    STATIC_URL = 'static/'
else:
    STATIC_ROOT = '/tmp/static'
    STATIC_URL = 'https://static.inabox.ies-sabadell.cat/static/'

# Uncomment to use hashed filenames with the cache framework.
#STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if DEBUG:
    MEDIA_ROOT = ''
    MEDIA_URL = ''
else:
    MEDIA_ROOT = '/tmp/media'
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

DEFAULT_FROM_EMAIL = SECRETS.get(
    "DEFAULT_FROM_EMAIL", "Inabox mailgoeshere")
EMAIL_BACKEND = SECRETS.get(
    "EMAIL_BACKEND",'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = SECRETS.get(
    "EMAIL_HOST", "smtp.gmail.com")
EMAIL_HOST_USER = SECRETS.get(
    "EMAIL_HOST_USER", "mailgoeshere")
EMAIL_HOST_PASSWORD = SECRETS.get(
    "EMAIL_HOST_PASSWORD", "your email password")
EMAIL_PORT = SECRETS.get(
    "EMAIL_PORT", 587)
EMAIL_USE_TLS = SECRETS.get(
    "EMAIL_USE_TLS", True)


BOOTSTRAP5 = {
    # The complete URL to the Bootstrap CSS file.
    # Note that a URL can be either a string
    # ("https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css"),
    # or a dict with keys `url`, `integrity` and `crossorigin` like the default value below.
    "css_url": {
        "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css",
        "integrity": "sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN",
        "crossorigin": "anonymous",
    },

    # The complete URL to the Bootstrap bundle JavaScript file.
    "javascript_url": {
        "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js",
        "integrity": "sha384-C6RzsynM9kWDrMNeT87bh95OGNyZPhcTNXj1NW7RuBCsyN/o0jlpcV8Qyq46cDfL",
        "crossorigin": "anonymous",
    },

    # The complete URL to the Bootstrap CSS theme file (None means no theme).
    "theme_url": None,

    # Put JavaScript in the HEAD section of the HTML document (only relevant if you use
    # bootstrap5.html).
    'javascript_in_head': False,

    # Wrapper class for non-inline fields.
    # The default value "mb-3" is the spacing as used by Bootstrap 5 example code.
    'wrapper_class': 'mb-3',

    # Wrapper class for inline fields.
    # The default value is empty, as Bootstrap5 example code doesn't use a wrapper class.
    'inline_wrapper_class': '',

    # Label class to use in horizontal forms.
    'horizontal_label_class': 'col-sm-2',

    # Field class to use in horizontal forms.
    'horizontal_field_class': 'col-sm-10',

    # Field class used for horizontal fields withut a label.
    'horizontal_field_offset_class': 'offset-sm-2',

    # Set placeholder attributes to label if no placeholder is provided.
    'set_placeholder': True,

    # Class to indicate required field (better to set this in your Django form).
    'required_css_class': '',

    # Class to indicate field has one or more errors (better to set this in your Django form).
    'error_css_class': '',

    # Class to indicate success, meaning the field has valid input (better to set this in your
    # Django form).
    'success_css_class': '',

    # Enable or disable Bootstrap 5 server side validation classes (separate from the indicator
    # classes above).
    'server_side_validation': True,

    # Renderers (only set these if you have studied the source and understand the inner workings).
    'formset_renderers':{
        'default': 'django_bootstrap5.renderers.FormsetRenderer',
    },
    'form_renderers': {
        'default': 'django_bootstrap5.renderers.FormRenderer',
    },
    'field_renderers': {
        'default': 'django_bootstrap5.renderers.FieldRenderer',
    },
}

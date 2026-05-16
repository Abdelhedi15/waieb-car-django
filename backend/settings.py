from pathlib import Path
from datetime import timedelta
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-33q@)3b-fl2_iefmum9s7l076p$r=szzlypmvy*1=6-pwxk1-a')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes',
    'django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
    'rest_framework','corsheaders','rest_framework_simplejwt',
    'accounts','vehicles','rentals','payments','contracts','tracking',
]
AUTH_USER_MODEL = 'accounts.User'
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware','django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware','django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'backend.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates','DIRS': [],'APP_DIRS': True,
    'OPTIONS': {'context_processors': ['django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'backend.wsgi.application'

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    import pymysql
    pymysql.version_info = (2, 2, 1, "final", 0)
    pymysql.install_as_MySQLdb()
    DATABASES = {'default': {'ENGINE': 'django.db.backends.mysql','NAME': 'car_rental_db',
        'USER': 'root','PASSWORD': '','HOST': '127.0.0.1','PORT': '3306',
        'OPTIONS': {'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",'charset': 'utf8mb4'}}}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
}
SIMPLE_JWT = {'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),'REFRESH_TOKEN_LIFETIME': timedelta(days=1),'AUTH_HEADER_TYPES': ('Bearer',)}
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Tunis'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = ['accept','accept-encoding','authorization','content-type','dnt','origin','user-agent','x-csrftoken','x-requested-with']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Mailjet — for client emails (confirmation, annulation)
MAILJET_API_KEY    = os.environ.get('MAILJET_API_KEY', '8ebdd344298e8697f7e755a77a00e9ab')
MAILJET_SECRET_KEY = os.environ.get('MAILJET_SECRET_KEY', '0ca860a4662fe85e035239de869e5949')
MAILJET_FROM_EMAIL = 'waiebcarrent2026@gmail.com'
MAILJET_FROM_NAME  = 'Waieb Car Rent'

# Resend — for forgot password only
RESEND_API_KEY   = os.environ.get('RESEND_API_KEY', 're_GfsnjSPu_JDbmqBTc5dfqTQyLdJA69rGa')
DEFAULT_FROM_EMAIL = 'Waieb Car Rent <onboarding@resend.dev>'

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
CSRF_TRUSTED_ORIGINS = ['https://web-production-e6e97.up.railway.app']


from pathlib import Path

from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-4un)))_xd9a6hnt-cr1l7i9x1ixdvn5-#060@ky_)o7!kc*8x4'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Thêm app jobs
    'jobs.apps.JobsConfig',
    # Phần để dùng trường PhoneNumberField
    'phonenumber_field',
    # Phần dùng cho Debug toolbar
    'debug_toolbar',
    # Phần CKEditor
    'ckeditor',
    'ckeditor_uploader',
    # API
    'rest_framework',
    # Phần Swagger
    'drf_yasg',
    # Phần OAuth2
    'oauth2_provider',
    # Phần filter
    'django_filters',
    'corsheaders',
    # 'django_redis'
    # 'rest_framework_simplejwt',

]

# SIMPLE_JWT = {
#     'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
#     'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
#     'ROTATE_REFRESH_TOKENS': False,
#     'BLACKLIST_AFTER_ROTATION': True,
#     'UPDATE_LAST_LOGIN': False,
#     'ALGORITHM': 'HS256',
#     'VERIFYING_KEY': None,
#     'AUTH_HEADER_TYPES': ('Bearer',),
#     'USER_ID_FIELD': 'id',
#     'USER_ID_CLAIM': 'user_id',
#     'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
#     'TOKEN_TYPE_CLAIM': 'token_type',
#     'JTI_CLAIM': 'jti',
# }

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    'corsheaders.middleware.CorsMiddleware',

]

# Hoặc cho phép tất cả nguồn nhưng yêu cầu credentials
CORS_ALLOW_ALL_ORIGINS = True  # Cần thêm điều này nếu sử dụng CORS_ALLOW_ALL_ORIGINS

# Cho phép gửi cookie cùng yêu cầu
CORS_ALLOW_CREDENTIALS = True

INTERNAL_IPS = [

    '127.0.0.1',

]

ROOT_URLCONF = 'jobPortal.urls'
MEDIA_ROOT = '%s/jobs/static' % BASE_DIR
CKEDITOR_UPLOAD_PATH = "ckeditor/images/"

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 300,
        'width': '100%',
    },
}

import os
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'job-referral/build')],
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

WSGI_APPLICATION = 'jobPortal.wsgi.application'

AUTH_USER_MODEL = 'jobs.User'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'jobdb',
        'USER': 'root',
        'PASSWORD': '123456',
        'HOST': ''
    }
}

# Phần upload ảnh lên Cloudinary
import cloudinary

cloudinary.config(
    cloud_name="dvxzmwuat",
    api_key="814652831379359",
    api_secret="BzgebW7M-yEgHzKWgEf176-MK6I"

)

REST_FRAMEWORK = {
    # Phần OAuth2
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        # 'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',  # Hoặc nguồn của frontend
]

# Cấu hình JWT
# SIMPLE_JWT = {
#     'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30), #Thời gian sống của access token.
#     'REFRESH_TOKEN_LIFETIME': timedelta(days=7), #Thời gian sống của refresh token
#     'ROTATE_REFRESH_TOKENS': True, #refresh token sẽ được làm mới mỗi khi access token được làm mới.
#     'BLACKLIST_AFTER_ROTATION': True, #refresh token cũ sẽ được đưa vào danh sách đen sau khi token mới được cấp phát
# }

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# OAUTH2_PROVIDER = {
#     'ACCESS_TOKEN_EXPIRE_SECONDS': 36000,
#     'AUTHORIZATION_CODE_EXPIRE_SECONDS': 600,
#     'OAUTH2_BACKEND_CLASS': 'oauth2_provider.oauth2_backends.JSONOAuthLibCore',
#     'SCOPES': {
#         'read': 'Read scope',
#         'write': 'Write scope',
#     },
# }

AUTHENTICATION_BACKENDS = (
    'oauth2_provider.backends.OAuth2Backend',
    'django.contrib.auth.backends.ModelBackend',
)


# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": "redis://192.168.1.219:6379/1",
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         }
#     }
# }

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'


STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'job-referral/build/static')
    ]

OAUTH2_PROVIDER = {
    'OAUTH2_BACKEND_CLASS': 'oauth2_provider.oauth2_backends.JSONOAuthLibCore'
}


CLIENT_ID = "8gMvsTseiW2YTOd9tik7q5VZxGNbhqdmY49qHkVU"
CLIENT_SECRET = "qLfzKj3gXRmzVk4s6guZrm1KPYelxZF3aqJKMSMXmc4Dv8QYGq4bhJhpkae0yN1Qf2C7jiT0IqXqLwBlxX4xYzcqjTdCYoBnuq760mUOGRxOuRw3Zi7hSW8IkSTIhWhf"


SITE_URL ='http://localhost:3000'

STRIPE_SECRET_KEY = 'sk_test_51PzHBhP5Uv4CEUblMyW7gjjY1QC6Z6A5i63X67uEOkVJwcxAuBQdMtMF2FyTiiNFgZnXiXd3Mw1bBUnUIOTHIbkb00u0hfE8Jk'

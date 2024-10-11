import os
import cloudinary
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # This loads the environment variables from the .env file

BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = int(os.environ.get("DEBUG", default=0))
DEBUG = os.environ.get("DEBUG", default='0').lower() in ['true', '1', 't', 'y', 'yes']

# ALLOWED_HOSTS = ['127.0.0.1', 'localhost',]
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost").split(" ")
print("Allowed hosts are:", ALLOWED_HOSTS)

# Application definition

INSTALLED_APPS = [
    'daphne',  # Daphne cho phép tạo và quản lý các kết nối WebSocket
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
    #CORS (Cross-Origin Resource Sharing)
    'corsheaders',
    # 'csp',
    'channels', # hỗ trợ các kết nối không đồng bộ,
]
OAUTH2_PROVIDER_APPLICATION_MODEL = 'oauth2_provider.Application'
OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL = 'oauth2_provider.AccessToken'
OAUTH2_PROVIDER_REFRESH_TOKEN_MODEL = 'oauth2_provider.RefreshToken'
OAUTH2_PROVIDER_ID_TOKEN_MODEL = 'oauth2_provider.IDToken'


ASGI_APPLICATION = "jobPortal.asgi.application"
WSGI_APPLICATION = 'jobPortal.wsgi.application'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',  # Địa chỉ Redis server và database 1
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}


# EMAIL_BACKEND = 'jobs.send-email.SendEmail'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')


REDIS_HOST = 'localhost'  # Địa chỉ host của Redis
REDIS_PORT = 6379         # Cổng mặc định của Redis

# Cho phép tất cả domain truy cập
CORS_ALLOW_ALL_ORIGINS = True

# Hoặc giới hạn chỉ một số domain
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',  # Domain front-end local,
    'http://localhost:8000',  # Domain backend-end local,
]

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
    'oauth2_provider.middleware.OAuth2TokenMiddleware',

]

INTERNAL_IPS = [
    '127.0.0.1',
    'localhost'
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

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
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

AUTH_USER_MODEL = 'jobs.User'

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': env('MYSQL_DATABASE'),
#         'USER': env('DATABASE_USER'),
#         'PASSWORD': env('DATABASE_PASSWORD'),
#         'HOST': env('DATABASE_HOST', default=''),
#         'PORT': env('DATABASE_PORT', default='3306'),
#     }
# }

DATABASES = {
    'default': {
        "ENGINE": os.environ.get("MYSQL_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("MYSQL_DATABASE", os.path.join(BASE_DIR, 'db.sqlite3')),
        'USER': os.environ.get('MYSQL_USER', 'myuser'),
        'PASSWORD': os.environ.get('MYSQL_PASSWORD', 'myuserpassword'),
        'HOST': os.environ.get('MYSQL_HOST', 'localhost'),
        'PORT': os.environ.get('MYSQL_PORT', default='3306'),
    }
}

# Phần upload ảnh lên Cloudinary
cloudinary.config(
    cloud_name="des7wmwn0",
    api_key="348292977468397",
    api_secret="9qJ5YCtTvXWQjRO_t4DGVf7k4JM",
)

REST_FRAMEWORK = {
    # Phần OAuth2
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',),
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',

}

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

# USE_I18N = True
# TIME_ZONE = 'UTC'

TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTHENTICATION_BACKENDS = (
    'oauth2_provider.backends.OAuth2Backend',
    'django.contrib.auth.backends.ModelBackend',
)

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"

OAUTH2_PROVIDER = {
    'OAUTH2_BACKEND_CLASS': 'oauth2_provider.oauth2_backends.JSONOAuthLibCore'
}

SITE_URL ='http://localhost:3000'

STRIPE_SECRET_KEY = 'sk_test_51PzHBhP5Uv4CEUblMyW7gjjY1QC6Z6A5i63X67uEOkVJwcxAuBQdMtMF2FyTiiNFgZnXiXd3Mw1bBUnUIOTHIbkb00u0hfE8Jk'

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
]

CLIENT_ID = "3Mj3P2rLZV34jTnqcn09cc0cAGAZATPjUfhO9ftG"
CLIENT_SECRET = "77sUVuOmGc5O2vwfxmCHZEEAJ6qfJBLYUMaKSti6jnhZ04GrL30DtLyLo5gcf6x1DxUJZiHV6Uf3ClH2NlyHVuHqjnxSFMr2ZwCktWWTfr3lF8YKN6VHJGTFZ6dYhnQv"

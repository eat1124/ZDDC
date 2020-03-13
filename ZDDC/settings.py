"""
Django settings for ZDDC project.

Generated by 'django-admin startproject' using Django 1.9.7.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
import djcelery

djcelery.setup_loader()
# BROKER_URL = 'django://'
# CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'

BROKER_URL = 'redis://:tesunet@223.247.155.54:6379/0'
# CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/1'
# BROKER_URL = 'amqp://root:password@localhost:5672/myvhost'

CELERY_TIMEZONE = 'Asia/Shanghai'  # 时区
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'  # 定时任务

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '%6n))bx30e&#b+hd!074=4)d!+4w3l(+dy28&%fh&mzv)i@nvr'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'datacenter',
    'djcelery',
    'kombu.transport.django',
]

MIDDLEWARE_CLASSES = [
    # 'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    # 'django.middleware.cache.FetchFromCacheMiddleware',
]

ROOT_URLCONF = 'ZDDC.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(os.path.dirname(__file__), 'templates').replace('\\', '/'), ],
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

TEMPLATE_LOADERS = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
]

WSGI_APPLICATION = 'ZDDC.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'datacenter_2',
        'USER': 'root',
        'PASSWORD': 'password',
        # 'HOST': '192.168.1.66',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
#
# DATABASES = {
#     'default': {
#         'ENGINE': 'sql_server.pyodbc',
#         'NAME': 'mkl',
#         'USER': 'miaokela',
#         'PASSWORD': 'Passw0rD',
#         'HOST': '127.0.0.1',
#         'PORT': '1433',
#         'OPTIONS': {
#             'driver': 'SQL Server Native Client 11.0',  # 這邊要去查詢作業系統本身支援的版本 Win10是 11
#         },
#     },
# }
# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
SITE_ROOT = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')
STATIC_ROOT = os.path.join(SITE_ROOT, 'static')

EMAIL_HOST = 'smtp.exmail.qq.com'
EMAIL_HOST_USER = 'huangzx@tesunet.com.cn'
EMAIL_HOST_PASSWORD = '00'
EMAIL_PORT = 25

# CASHES_DIR = BASE_DIR + os.sep + "faconstor"+ os.sep + "static"+ os.sep + "mem"
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
#         'LOCATION': CASHES_DIR,  # 设置缓存文件的目录
#         'OPTIONS': {
#             'MAX_ENTRIES': 300,  # 最大缓存个数（默认300）
#             'CULL_FREQUENCY': 3,  # 缓存到达最大个数之后，剔除缓存个数的比例，即：1/CULL_FREQUENCY（默认3）
#         },
#     }
# }


# 日志系统
# 创建日志的路径
LOG_PATH = os.path.join(BASE_DIR, 'log')
# 如果地址不存在，则自动创建log文件夹
if not os.path.exists(LOG_PATH):
    os.mkdir(LOG_PATH)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,   # True表示禁用logger
    'formatters': {
        'default': {
            'format': '%(levelno)s %(module)s %(asctime)s %(message)s ',
            'datefmt': '%Y-%m-%d %A %H:%M:%S',
        },
    },

    'handlers': {
        'process_handlers': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',  # 日志文件指定为5M, 超过5m重新命名，然后写入新的日志文件
            'maxBytes': 5 * 1024,  # 指定文件大小
            'filename': '%s/process.txt' % LOG_PATH,  # 指定文件地址
            'formatter': 'default',
            'encoding': 'utf8',
        },
    },
    'loggers': {
        'process': {
            'handlers': ['process_handlers'],
            'level': 'INFO'
        },
    },
}



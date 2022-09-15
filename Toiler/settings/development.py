import os
import sys
from .base import MIDDLEWARE, INSTALLED_APPS

DEBUG = True

EMAIL_HOST = '127.0.0.1'
EMAIL_PORT = 1025

INTERNAL_IPS = [
    "127.0.0.1",
]
CSRF_TRUSTED_ORIGINS = ['https://localhost', ]

DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    # }

    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            # 'read_default_file': BASE_DIR+'database.conf',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'; SET default_storage_engine=INNODB",
            'isolation_level': 'read committed'
        },
        'NAME': 'toiler_db',
        'USER': 'app_user',
        'PASSWORD': os.environ['MYSQL_PASSWORD'],
        'HOST': 'toiler-db',  # its loopback
        'PORT': '3306',
        'CONN_MAX_AGE': 5,  # seconds
    }
    ,
}

MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
INSTALLED_APPS.append('debug_toolbar')


if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test_database'
    }

NOSE_ARGS = ['--nocapture',
             '--nologcapture']

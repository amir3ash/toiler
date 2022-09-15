import os

DEBUG = False

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'toiler.ir', 'www.toiler.ir']
CSRF_TRUSTED_ORIGINS = ['https://localhost']

EMAIL_HOST = 'smtp-relay.sendinblue.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True

EMAIL_API_PASSWORD = os.environ['EMAIL_API_PASSWORD']


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            # 'init_command': "SET sql_mode='STRICT_TRANS_TABLES'; SET default_storage_engine=INNODB",
            'isolation_level': 'read committed'
        },
        'NAME': 'toiler_db',
        'USER': os.environ.get('MYSQL_USER', 'app_user'),
        'PASSWORD': os.environ['MYSQL_PASSWORD'],
        'HOST': 'toiler-db',
        'PORT': '3306',
        'CONN_MAX_AGE': 5,  # seconds
    }
}

# STATIC_ROOT = os.path.join(BASE_DIR, 'static')

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True

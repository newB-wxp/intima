# -*- coding: utf-8 -*-

import os
import re
import socket
import datetime
from .enum import Enum
from celery.schedules import crontab


_basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
TEMPLATE_DIR = os.path.join(_basedir, 'application', 'templates')


E = Enum(['development', 'production', 'test'])
APP_NAME = Enum(['maybi', 'worker', 'admin'])


class BaseConfig(object):

    PROJECT = APP_NAME.maybi
    VERSION = '2026.07.16'
    DEBUG = True
    TESTING = False
    PROD = False

    # ===========================================
    # Dev Mode
    # DEV_MODE=True: 跳过第三方OAuth和真实支付
    # DEV_MODE=False: 生产模式
    DEV_MODE = os.environ.get('DEV_MODE', 'true').lower() == 'true'

    # Flask Toolbar
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    DEBUG_TB_TEMPLATE_EDITOR_ENABLED = True
    DEBUG_TB_PROFILER_ENABLED = True
    DEBUG_TB_PANELS = [
        'flask_debugtoolbar.panels.versions.VersionDebugPanel',
        'flask_debugtoolbar.panels.timer.TimerDebugPanel',
        'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
        'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
        'flask_debugtoolbar.panels.config_vars.ConfigVarsDebugPanel',
        'flask_debugtoolbar.panels.template.TemplateDebugPanel',
        'flask_debugtoolbar.panels.logger.LoggingPanel',
        'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel',
    ]

    ENV = E.development

    ADMINS = frozenset(['season@maybi.cn'])

    SECRET_KEY = os.environ.get('SECRET_KEY', 'WhatIsTheMeaningOfLife')
    IDCARD_KEY = os.environ.get('IDCARD_KEY', 'HowAreYouDoing')
    CSRF_ENABLED = True
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = False
    WTF_CSRF_TIME_LIMIT = 3600

    UPLOAD_FOLDER = os.path.join(_basedir, 'application', 'static/csv/')
    AVATAR_FOLDER = os.path.join(_basedir, 'application/static/img/avatar')

    # ===========================================
    # Session
    REMEMBER_COOKIE_DOMAIN = '.maybi.cn'
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=31)

    # ===========================================
    # MongoDB Atlas (SRV connection string)
    #
    # Format: mongodb+srv://user:pass@cluster.mongodb.net/bibi?retryWrites=true&w=majority
    MONGODB_URI = os.environ.get(
        'MONGODB_URI',
        'mongodb+srv://user:pass@cluster.mongodb.net/bibi?retryWrites=true&w=majority'
    )

    # Optional TLS cert for Atlas
    MONGO_CA_CERT = os.environ.get('MONGO_CA_CERT', '')

    MONGODB_SETTINGS = {
        'db': 'bibi',
        'host': MONGODB_URI,
        'connect': False,
    }

    ORDER_DB_CONFIG = {
        'alias': 'order_db',
        'name': 'order',
        'host': MONGODB_URI,
    }

    INVENTORY_DB_CONFIG = {
        'alias': 'inventory_db',
        'name': 'inventory',
        'host': MONGODB_URI,
    }

    CART_DB_CONFIG = {
        'alias': 'cart_db',
        'name': 'cart',
        'host': MONGODB_URI,
    }

    CONTENT_DB_CONFIG = {
        'alias': 'content_db',
        'name': 'content',
        'host': MONGODB_URI,
    }

    LOG_DB_CONFIG = {
        'alias': 'log_db',
        'name': 'order',
        'host': MONGODB_URI,
    }

    # ===========================================
    # Upstash Redis (TLS — rediss://)
    #
    # Format: rediss://:token@host.upstash.io:port
    _redis_url = os.environ.get(
        'REDIS_URL',
        'rediss://:token@host.upstash.io:6379'
    )

    REDIS_CONFIG = {
        'host': _redis_url.split('@')[1].split(':')[0] if '@' in _redis_url else 'localhost',
        'port': int(_redis_url.split(':')[-1]) if ':' in _redis_url.rsplit('@', 1)[-1] else 6379,
        'db': 0,
        'ssl': True,
        'ssl_cert_reqs': None,
    }

    SESSION_REDIS = {
        'host': REDIS_CONFIG['host'],
        'port': REDIS_CONFIG['port'],
        'db': 0,
        'ssl': True,
        'ssl_cert_reqs': None,
        'encoding': 'utf-8',
        'encoding_errors': 'strict',
        'decode_responses': False,
    }

    MONGO_INVENTORY_DBNAME = 'inventory'
    MONGO_INVENTORY_URI = MONGODB_URI.replace('/bibi', '/inventory')

    # ===========================================
    # Flask-mail
    MAIL_DEBUG = False
    MAIL_SERVER = ''
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = ''
    MAIL_PASSWORD = ''
    DEFAULT_MAIL_SENDER = MAIL_USERNAME

    # ===========================================
    # Flask-babel
    ACCEPT_LANGUAGES = ['zh', 'en']
    BABEL_DEFAULT_LOCALE = 'zh'

    # ===========================================
    # Security Headers (Flask-Talisman)
    TALISMAN_ENABLED = os.environ.get('TALISMAN_ENABLED',
        'false' if DEV_MODE else 'true').lower() == 'true'
    TALISMAN_CONFIG = {
        'force_https': not DEV_MODE,
        'session_cookie_secure': not DEV_MODE,
        'session_cookie_http_only': True,
        'session_cookie_samesite': 'Lax',
        'content_security_policy': {
            'default-src': "'self'",
            'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'",
                           'https://cdn.jsdelivr.net', 'https://cdnjs.cloudflare.com'],
            'style-src': ["'self'", "'unsafe-inline'",
                          'https://cdn.jsdelivr.net', 'https://cdnjs.cloudflare.com',
                          'https://fonts.googleapis.com'],
            'font-src': ["'self'", 'https://fonts.gstatic.com', 'https://cdnjs.cloudflare.com'],
            'img-src': ["'self'", 'data:', 'blob:', 'https:', 'http:'],
            'connect-src': ["'self'", 'https:', 'wss:'],
            'frame-src': ["'self'"],
            'object-src': "'none'",
            'base-uri': "'self'",
            'form-action': "'self'",
        },
        'content_security_policy_nonce_in': [],
        'strict_transport_security': not DEV_MODE,
        'strict_transport_security_max_age': 31536000,
        'strict_transport_security_include_subdomains': True,
        'x_content_type_options': True,
        'x_frame_options': 'DENY',
        'referrer_policy': 'strict-origin-when-cross-origin',
    }

    # ===========================================
    # Flask-cache
    CACHE_TYPE = 'redis'

    TRACKING_EXCLUDE = (
        '^/favicon.ico',
        '^/static/',
        '^/admin/',
        '^/_debug_toolbar/',
    )

    # ===========================================
    # Celery (Upstash Redis as broker)
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', _redis_url)
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', _redis_url)

    CELERY_IMPORTS = (
        'application.services.jobs.image',
        'application.services.jobs.noti',
        'application.services.jobs.express',
        'application.services.scheduling.forex',
        'application.services.scheduling.express',
    )

    CELERYD_TASK_TIME_LIMIT = 300
    CELERYD_TASK_SOFT_TIME_LIMIT = 120
    CELERYD_OPTS = "--time-limit=300 --concurrency=1"

    CELERYBEAT_SCHEDULE = {
        'record_latest_forex_rate_every_2_hours': {
            'task': 'application.services.scheduling.forex.record_latest_forex_rate',
            'schedule': crontab(minute=0, hour="*/2"),
        },
        'kuaidi_request_every_8_hour': {
            'task': 'application.services.scheduling.express.check_kuaidi',
            'schedule': crontab(minute=0, hour="*/8"),
        },
    }

    # ===========================================
    # Bibi Phase 1: OAuth (Authlib — Google + Facebook only)
    #
    # Google:       https://console.cloud.google.com/apis/credentials
    # Facebook:     https://developers.facebook.com
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID', '')
    FACEBOOK_APP_SECRET = os.environ.get('FACEBOOK_APP_SECRET', '')
    OAUTH_REDIRECT_BASE = os.environ.get('OAUTH_REDIRECT_BASE', 'http://localhost:5000')

    # ===========================================
    # Bibi Phase 1: Payment (Adult Three-Channel)
    #
    # CCBill:     https://ccbill.com        (US/CA/GB, ~10.8-14.5%)
    # EcomCharge: https://ecomcharge.com     (EU, 3.5-5%)
    # WcPay:      https://wcpay.io           (Global fallback, USDC settlement)
    CCBILL_ACCOUNT_ID = os.environ.get('CCBILL_ACCOUNT_ID', '')
    CCBILL_API_KEY = os.environ.get('CCBILL_API_KEY', '')
    ECOMCHARGE_API_KEY = os.environ.get('ECOMCHARGE_API_KEY', '')
    WCPAY_API_KEY = os.environ.get('WCPAY_API_KEY', '')
    PAYMENT_SANDBOX = os.environ.get('PAYMENT_SANDBOX', 'true').lower() == 'true'

    # ===========================================
    # Monitoring (Sentry)
    #
    # Sentry DSN — https://sentry.io
    # 留空禁用错误监控。免费额度：5,000 errors/月
    SENTRY_DSN = os.environ.get('SENTRY_DSN', '')

    # ===========================================
    # App
    APP_VERSION = '2.0.0'
    ENV_STR = os.environ.get('ENV', 'development')
    SITE_URL = os.environ.get('SITE_URL', 'http://localhost:5000')

    # ===========================================
    # Upstash Redis URL (完整字符串)
    REDIS_URL = os.environ.get('REDIS_URL', _redis_url)


class ProdConfig(BaseConfig):
    DEBUG = True
    PROD = True
    ENV = E.production


class DevConfig(BaseConfig):
    DEBUG = True
    ENV = E.development
    ASSETS_DEBUG = True
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


class TestConfig(DevConfig):
    TESTING = True
    ENV = E.test
    CACHE_TYPE = 'null'
    CACHE_NO_NULL_WARNING = True


config_map = {
    'development': DevConfig,
    'test': TestConfig,
    'production': ProdConfig,
}


def get_config(env, app=''):
    if app == 'worker':
        env = 'production'
    return config_map[env]()


def get_config_from_host(app_name):
    flask_env = os.environ.get('FLASK_ENV', 'production')
    config = get_config(flask_env, app_name)
    return config

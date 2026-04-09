import os
from pathlib import Path
import environ

env = environ.Env()
environ.Env.read_env(os.path.join(Path(__file__).resolve().parent.parent, '.env'))

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

SITE_URL = env('SITE_URL', default='http://localhost:8000')
#SITE_URL = 'https://omnichannel.autos'
#SITE_URL = 'http://localhost:8000'

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sites',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'django_extensions',
    'django_htmx',
    'debug_toolbar',                     # local development only
    'auditlog',
    'allauth',
    'allauth.account',
 #   'allauth.socialaccount',
    'django_celery_beat',
    'django_celery_results',
    'django_filters',
    'django_tables2',
    # 'django_tailwind_cli',
    'crispy_forms',
    'crispy_tailwind',
    "modern_csrf",
    # Local apps
    'accounts',
    'customers',
    'products',
    'tickets',
    'public',
    'integration',
    'notifications',
    'analytics',
    'utilities',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',  # local
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    "modern_csrf.middleware.ModernCsrfViewMiddleware",
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',            # HTMX
    'auditlog.middleware.AuditlogMiddleware',           # Auditlog
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'core.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
    }
}

# Custom user model
AUTH_USER_MODEL = 'accounts.User'
SITE_ID = 1

# Password validation
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

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'handlers': {
#         'celery_file': {
#             'level': 'DEBUG',
#             'class': 'logging.FileHandler',
#             'filename': '/tmp/celery.log',   # change to a path you have write access to
#         },
#         'console': {
#             'class': 'logging.StreamHandler',
#         },
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['console'],
#             'level': 'INFO',
#         },
#         'allauth': {
#             'handlers': ['console'],
#             'level': 'DEBUG',
#         },
#         'celery': {
#             'handlers': ['celery_file', 'console'],
#             'level': 'DEBUG',
#         },
#         'celery.task': {
#             'handlers': ['celery_file', 'console'],
#             'level': 'DEBUG',
#         },
#         'celery.worker': {
#             'handlers': ['console'],
#             'level': 'WARNING',
#         },
#         'celery.beat': {
#             'handlers': ['console'],
#             'level': 'WARNING',
#         },
#     },
# }

ACCOUNT_FORMS = {
    'login': 'accounts.forms.CustomLoginForm',
    'signup': 'accounts.forms.CustomSignupForm',
    'reset_password': 'accounts.forms.CustomResetPasswordForm',
    'change_password': 'accounts.forms.CustomChangePasswordForm',
    'reset_password_from_key': 'accounts.forms.CustomResetPasswordKeyForm',
    # ... other forms
    
    # etc.
}

# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
EMAIL_HOST_USER = 'apikey' # this is exactly the value 'apikey'
DEFAULT_FROM_EMAIL=os.getenv('DEFAULT_FROM_EMAIL')
SENDGRID_SANDBOX_MODE_IN_DEBUG = False

# EMAIL_BACKEND = "sendgrid_backend.SendgridBackend"
# EMAIL_HOST = 'smtp.sendgrid.net'
# EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST = env('EMAIL_HOST')
# EMAIL_PORT = env.int('EMAIL_PORT')
# EMAIL_HOST_USER = env('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
# EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS')
# DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@localhost')
# DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
# You can leave EMAIL_HOST_USER and EMAIL_HOST_PASSWORD blank for MailHog
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

ACCOUNT_FORMS = {
    'login': 'accounts.forms.CustomLoginForm',
    'signup': 'accounts.forms.CustomSignupForm',
    'reset_password': 'accounts.forms.CustomResetPasswordForm',
    'change_password': 'accounts.forms.CustomChangePasswordForm',
    'reset_password_from_key': 'accounts.forms.CustomResetPasswordKeyForm',
    # ... other forms
    
    # etc.
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# Use a leading slash so `{% static %}` produces absolute paths like `/static/...`
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Tailwind CLI (django-tailwind-cli)
TAILWIND_CLI_PATH = BASE_DIR / 'static' / 'css'   # where output.css will be placed
TAILWIND_CLI_CONFIG_FILE = BASE_DIR.parent / 'frontend' / 'tailwind.config.js'
TAILWIND_CLI_SRC_CSS = BASE_DIR.parent / 'frontend' / 'src' / 'input.css'
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# Celery
CELERY_BROKER_URL = env('REDIS_URL')
CELERY_RESULT_BACKEND = 'django-db'  # use django-celery-results
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_TASK_ALWAYS_EAGER = True  # for development, tasks run synchronously
CELERY_WORKER_LOG_LEVEL = 'WARNING'
CELERY_WORKER_REDIRECT_STDOUTS_LEVEL = 'WARNING'

# Django Debug Toolbar (local only)
INTERNAL_IPS = ['127.0.0.1']

DJANGO_TABLES2_TABLE_ATTRS = {
    "class": "min-w-full bg-white shadow divide-y divide-gray-200 overflow-hidden sm:rounded-lg",
    "thead": {
        "class": "bg-gray-50",
    },
    "tbody": {
        "class": "bg-white divide-y divide-gray-200",
    },
    "th": {
        "class": "px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
    },
    "td": {
        "class": "px-6 py-4 whitespace-nowrap text-sm text-gray-900",
    },
    "tr": {
        "class": "bg-white hover:bg-gray-100",  # lighter hover
    },
}

# django-allauth configuration (if used)
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Any other settings...
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

LOGIN_REDIRECT_URL = "/"
# LOGOUT_REDIRECT_URL = "/accounts/login/"

# Allauth settings
# ACCOUNT_AUTHENTICATION_METHOD = 'username_email'  # or 'username', 'email'
# ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # or 'optional' or 'mandatory'
# ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_CONFIRMATION_HMAC = True   # default
ACCOUNT_CONFIRM_EMAIL_ON_GET = False
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3

# ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
ACCOUNT_LOGOUT_REDIRECT_URL = '/'          # after logout
LOGIN_REDIRECT_URL = '/dashboard/'         # after login
LOGIN_URL = '/accounts/login/'
ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_ADAPTER = 'accounts.adapters.CeleryAccountAdapter'

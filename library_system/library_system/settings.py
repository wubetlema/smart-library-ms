import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Load .env file if present ─────────────────────────────────────────────────
def _env(key, default=''):
    """Read from environment or .env file."""
    if key in os.environ:
        return os.environ[key]
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                if k.strip() == key:
                    return v.strip()
    return default


# ── Core ──────────────────────────────────────────────────────────────────────
SECRET_KEY = _env('SECRET_KEY', 'django-insecure-dev-only-change-in-production')
DEBUG = _env('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = [h.strip() for h in _env('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'accounts',
    'books',
    'borrowing',
    'activity',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'activity.middleware.ActivityLogMiddleware',
    'activity.middleware.NoCacheMiddleware',
]

ROOT_URLCONF = 'library_system.urls'

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

WSGI_APPLICATION = 'library_system.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': _env('DB_NAME', 'library_db'),
        'USER': _env('DB_USER', 'root'),
        'PASSWORD': _env('DB_PASSWORD', ''),
        'HOST': _env('DB_HOST', '127.0.0.1'),
        'PORT': _env('DB_PORT', '3306'),
        'OPTIONS': {
            'sql_mode': 'STRICT_TRANS_TABLES',
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.CustomUser'

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/accounts/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# ── Email ─────────────────────────────────────────────────────────────────────
_email_user = _env('EMAIL_HOST_USER', '')
if _email_user:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = _email_user
    EMAIL_HOST_PASSWORD = _env('EMAIL_HOST_PASSWORD', '')
else:
    # Dev fallback — prints emails to console
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = 'LibraryMS <noreply@libraryms.com>'

# ── Security ──────────────────────────────────────────────────────────────────
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'

# Rate limiting: max login attempts tracked via session
LOGIN_ATTEMPT_LIMIT = 5

# ── App settings ──────────────────────────────────────────────────────────────
FINE_PER_DAY = 5.00
MAX_BORROW_LIMIT = 3
PASSWORD_RESET_TIMEOUT = 3600  # 1 hour

from .base import *
from .base import env, BASE_DIR

DEBUG = True
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="dev-secret-key-change-in-production",
)
ALLOWED_HOSTS = ["*"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'ATOMIC_REQUESTS': True,
    }
}

EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend"
)

INSTALLED_APPS = ["whitenoise.runserver_nostatic"] + INSTALLED_APPS
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2", "localhost"]
INSTALLED_APPS += ["django_extensions"]

# Disable all HTTPS enforcement in development
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

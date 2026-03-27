from .base import *
from .base import env, BASE_DIR

SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="test-secret-key-for-testing-only",
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_test.sqlite3',
        'ATOMIC_REQUESTS': True,
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
TEMPLATES[0]["OPTIONS"]["debug"] = True
MEDIA_URL = 'http://media.testserver/'  # Must end with slash

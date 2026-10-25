"""
Django settings for the consolidated Ingenio platform (SII + Ventas + Aula).
"""

from pathlib import Path
from decouple import config
import os
import sys

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="#%9g2p3)pba4-h0$b5bi5vw$q%lx%#x*odh&xk%$hl6td^kh#2")

DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "testserver",
    ".vercel.app",
    "blog.juampamillan.com",
    ".github.dev",
    ".modeloingenio.xyz",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "sii",
    "usuario",
    "ventas.apps.VentasConfig",
    "aula.apps.AulaConfig",
    "docente",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "api.middleware.auto_migrate.AutoMigrateMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "sii.middleware.FeatureAccessMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "api.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "api.context_processors.ingenio_shell",
            ],
        },
    },
]

WSGI_APPLICATION = "api.wsgi.app"

_skip_postgres = (
    "test" in sys.argv
    or "collectstatic" in sys.argv
    or os.environ.get("DJANGO_TEST") == "1"
    or os.environ.get("COLLECTSTATIC") == "1"
    or os.environ.get("DJANGO_SQLITE") == "1"
)
if _skip_postgres:
    if os.environ.get("DJANGO_SQLITE") == "1":
        _default_db = str(BASE_DIR / "demo.sqlite3")
        _auth_db = str(BASE_DIR / "demo_auth.sqlite3")
    else:
        _default_db = ":memory:"
        _auth_db = ":memory:"
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": _default_db,
        },
        "auth": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": _auth_db,
        },
    }
    MIDDLEWARE = [item for item in MIDDLEWARE if "auto_migrate" not in item]
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("DB_NAME"),
            "USER": config("DB_USER"),
            "PASSWORD": config("DB_PASSWORD"),
            "HOST": config("DB_HOST"),
            "PORT": config("DB_PORT", default="5432"),
            "OPTIONS": {"sslmode": "require"},
        },
        "auth": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("AUTH_NAME"),
            "USER": config("AUTH_USER"),
            "PASSWORD": config("AUTH_PASSWORD"),
            "HOST": config("AUTH_HOST"),
            "PORT": config("AUTH_PORT", default="5432"),
            "OPTIONS": {"sslmode": "require"},
        },
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
# Si el deploy olvida collectstatic, WhiteNoise igual encuentra static/ y las apps.
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Archivos (entregas y materiales). En Vercel el disco local no persiste.
BLOB_READ_WRITE_TOKEN = config("BLOB_READ_WRITE_TOKEN", default="")
VERCEL_BLOB_READ_WRITE_TOKEN = config("VERCEL_BLOB_READ_WRITE_TOKEN", default="")
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="")
AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="")
AWS_S3_ENDPOINT_URL = config("AWS_S3_ENDPOINT_URL", default="") or None
AWS_S3_CUSTOM_DOMAIN = config("AWS_S3_CUSTOM_DOMAIN", default="") or None
AWS_QUERYSTRING_AUTH = config("AWS_QUERYSTRING_AUTH", default=True, cast=bool)
AWS_DEFAULT_ACL = None
AWS_S3_FILE_OVERWRITE = False


def _storage_backend():
    elegido = config("STORAGE_BACKEND", default="").strip().lower()
    tiene_blob = bool(BLOB_READ_WRITE_TOKEN or VERCEL_BLOB_READ_WRITE_TOKEN)
    tiene_s3 = bool(AWS_STORAGE_BUCKET_NAME)
    if not elegido:
        if tiene_blob:
            elegido = "vercel_blob"
        elif tiene_s3:
            elegido = "s3"
        else:
            elegido = "local"
    if elegido in {"vercel", "blob", "vercel_blob"}:
        if tiene_blob:
            return "aula.storage.VercelBlobStorage"
        if DEBUG:
            return "django.core.files.storage.FileSystemStorage"
        return "aula.storage.VercelBlobStorage"
    if elegido == "s3":
        if tiene_s3:
            if "storages" not in INSTALLED_APPS:
                INSTALLED_APPS.append("storages")
            return "storages.backends.s3boto3.S3Boto3Storage"
        if DEBUG:
            return "django.core.files.storage.FileSystemStorage"
        return "storages.backends.s3boto3.S3Boto3Storage"
    return "django.core.files.storage.FileSystemStorage"


STORAGES = {
    "default": {"BACKEND": _storage_backend()},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

CSRF_TRUSTED_ORIGINS = [
    "https://*.vercel.app",
    "https://*.modeloingenio.xyz",
    "https://sii.modeloingenio.xyz",
    "https://blog.juampamillan.com",
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATABASE_ROUTERS = ["api.dbrouters.auth_router.AuthRouter"]

LOGIN_REDIRECT_URL = "/inicio/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = "/"

EMAIL_BACKEND = config(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="Ingenio <no-reply@modeloingenio.xyz>")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "sii.permissions.EsAdministradorAPI",
    ],
}

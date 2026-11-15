"""
Django settings for the consolidated Ingenio platform (SII + Ventas + Aula).
"""

from pathlib import Path
from decouple import config
import os
import sys

from api.envflags import resolver_debug
from aula.storage import DEFAULT_BUCKET, DEFAULT_REGION, backend_archivos

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="#%9g2p3)pba4-h0$b5bi5vw$q%lx%#x*odh&xk%$hl6td^kh#2")

DEBUG = resolver_debug(os.environ.get("VERCEL_ENV"), config("DEBUG", default="False"))

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
    "storages",
    "rest_framework",
    "sii",
    "usuario",
    "ventas.apps.VentasConfig",
    "aula.apps.AulaConfig",
    "campus.apps.CampusConfig",
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

_test_en_postgres = os.environ.get("DJANGO_TEST_POSTGRES") == "1"
_skip_postgres = not _test_en_postgres and (
    "test" in sys.argv
    or "collectstatic" in sys.argv
    or os.environ.get("DJANGO_TEST") == "1"
    or os.environ.get("COLLECTSTATIC") == "1"
    or os.environ.get("DJANGO_SQLITE") == "1"
)


def _postgres(name_key, user_key, password_key, host_key, port_key, ssl_key):
    sslmode = config(ssl_key, default=config("DB_SSLMODE", default="require"))
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config(name_key),
        "USER": config(user_key),
        "PASSWORD": config(password_key, default=""),
        "HOST": config(host_key),
        "PORT": config(port_key, default="5432"),
        "OPTIONS": {"sslmode": sslmode},
    }


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
        "default": _postgres("DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_SSLMODE"),
        "auth": _postgres("AUTH_NAME", "AUTH_USER", "AUTH_PASSWORD", "AUTH_HOST", "AUTH_PORT", "AUTH_SSLMODE"),
    }
    if _test_en_postgres or "test" in sys.argv:
        MIDDLEWARE = [item for item in MIDDLEWARE if "auto_migrate" not in item]

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

# Neon Object Storage (S3 path-style, bucket privado + signed URLs).
# Mismo naming que Bodamos. En Vercel el disco local no persiste.
NEON_S3_ENDPOINT = config("NEON_S3_ENDPOINT", default="")
NEON_S3_REGION = config("NEON_S3_REGION", default=DEFAULT_REGION) or DEFAULT_REGION
NEON_S3_ACCESS_KEY_ID = config("NEON_S3_ACCESS_KEY_ID", default="")
NEON_S3_SECRET_ACCESS_KEY = config("NEON_S3_SECRET_ACCESS_KEY", default="")
NEON_S3_BUCKET = config("NEON_S3_BUCKET", default=DEFAULT_BUCKET) or DEFAULT_BUCKET

AWS_S3_ENDPOINT_URL = NEON_S3_ENDPOINT or None
AWS_S3_REGION_NAME = NEON_S3_REGION
AWS_ACCESS_KEY_ID = NEON_S3_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = NEON_S3_SECRET_ACCESS_KEY
AWS_STORAGE_BUCKET_NAME = NEON_S3_BUCKET
AWS_S3_ADDRESSING_STYLE = "path"
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_QUERYSTRING_AUTH = True
AWS_DEFAULT_ACL = None
AWS_S3_FILE_OVERWRITE = False

STORAGES = {
    "default": {
        "BACKEND": backend_archivos(
            endpoint=NEON_S3_ENDPOINT,
            access_key=NEON_S3_ACCESS_KEY_ID,
            secret_key=NEON_S3_SECRET_ACCESS_KEY,
            force_local=config("STORAGE_BACKEND", default="").strip().lower() == "local",
        )
    },
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

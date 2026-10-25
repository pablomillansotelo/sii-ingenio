"""Resolución de archivos: Neon Object Storage (S3 path-style) o disco local."""

S3_BACKEND = "storages.backends.s3boto3.S3Boto3Storage"
LOCAL_BACKEND = "django.core.files.storage.FileSystemStorage"
DEFAULT_BUCKET = "aula"
DEFAULT_REGION = "us-east-2"


def neon_configurado(endpoint="", access_key="", secret_key=""):
    return bool(
        str(endpoint or "").strip()
        and str(access_key or "").strip()
        and str(secret_key or "").strip()
    )


def backend_archivos(*, endpoint="", access_key="", secret_key="", force_local=False):
    """Producción: Neon si hay endpoint + keys. Si no, disco local (DEBUG / tests)."""
    if force_local:
        return LOCAL_BACKEND
    if neon_configurado(endpoint, access_key, secret_key):
        return S3_BACKEND
    return LOCAL_BACKEND

from django.core.wsgi import get_wsgi_application
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")

app = get_wsgi_application()

try:
    from api.middleware.auto_migrate import apply_pending_migrations

    apply_pending_migrations()
except Exception:
    pass

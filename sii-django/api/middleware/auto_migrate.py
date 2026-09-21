import logging
import threading

from django.core.management import call_command

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_migrate_done = False


def apply_pending_migrations():
    """Aplica migraciones una vez por instancia serverless (Neon/Vercel)."""
    global _migrate_done
    if _migrate_done:
        return
    with _lock:
        if _migrate_done:
            return
        try:
            call_command("migrate", "--noinput", "--fake-initial", verbosity=0)
            call_command("migrate", "--database=auth", "--noinput", "--fake-initial", verbosity=0)
        except Exception:
            logger.exception("No se pudieron aplicar las migraciones al iniciar")
        finally:
            _migrate_done = True


class AutoMigrateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        apply_pending_migrations()
        return self.get_response(request)

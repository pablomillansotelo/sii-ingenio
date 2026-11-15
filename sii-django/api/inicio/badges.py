from django.db import connection
from django.utils import timezone

from api.inicio.cache import memo_user


def _scalar(sql, params=None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        row = cursor.fetchone()
        return int(row[0] or 0) if row else 0


def contar_contexto(user, contexto, hoy=None):
    hoy = hoy or timezone.localdate()
    return memo_user(user, f"badge:{contexto}:{hoy}", lambda: _contar(user, contexto, hoy))


def _contar(user, contexto, hoy):
    if contexto == "escolar":
        return _scalar(
            """
            SELECT (
              (SELECT COUNT(*) FROM tra_solicitud_baja WHERE estado = 'enviada')
              + (SELECT COUNT(*) FROM tra_documento_expediente WHERE estado = 'en_revision')
              + (SELECT COUNT(*) FROM campus_ticket_ayuda WHERE estado IN ('abierto', 'en_atencion'))
            )
            """
        )
    if contexto == "ventas":
        return _scalar(
            """
            SELECT (
              (SELECT COUNT(*) FROM tra_venta WHERE estado = 'confirmada' AND estado_pago IN ('pendiente', 'parcial'))
              + (SELECT COUNT(*) FROM solicitud_oferta WHERE estado = 'enviada')
            )
            """
        )
    if contexto == "docente":
        from api.inicio.widgets_docente import _curso_ids
        from aula.services import entregas_pendientes_qs

        ids = _curso_ids(user)
        if not ids:
            return 0
        return entregas_pendientes_qs(user).filter(actividad__curso_id__in=ids).count()
    if contexto == "direccion":
        return _scalar(
            """
            SELECT (
              (SELECT COUNT(*) FROM tra_solicitud_baja WHERE estado = 'enviada')
              + (SELECT COUNT(*) FROM tra_documento_expediente WHERE estado = 'en_revision')
              + (SELECT COUNT(*) FROM campus_ticket_ayuda WHERE estado IN ('abierto', 'en_atencion'))
              + (SELECT COUNT(*) FROM tra_venta WHERE estado = 'confirmada' AND estado_pago IN ('pendiente', 'parcial'))
            )
            """
        )
    return 0

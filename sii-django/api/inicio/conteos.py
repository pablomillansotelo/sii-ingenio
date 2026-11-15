from django.db import connection

from api.inicio.cache import memo_user
from sii.identity import alumnos_visibles
from sii.rbac import has_feature, scope_for


def _fetch(sql, params=None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        return cursor.fetchone()


def conteos_para(user, contexto):
    return memo_user(user, f"conteos:{contexto}", lambda: _conteos(user, contexto))


def _conteos(user, contexto):
    chips = []
    if contexto == "ventas":
        row = _fetch(
            """
            SELECT
              (SELECT COUNT(*) FROM cat_cliente WHERE activo = 1),
              (SELECT COUNT(*) FROM cat_producto WHERE activo = 1),
              (SELECT COUNT(*) FROM cat_edicion_curso WHERE activo = 1 AND estado IN ('programada', 'en_curso'))
            """
        )
        clientes, cursos, ediciones = row or (0, 0, 0)
        if has_feature(user, "ventas.clientes"):
            chips.append({"label": "Clientes activos", "value": clientes, "url_name": "Clientes"})
        if has_feature(user, "ventas.cursos"):
            chips.append({"label": "Cursos en venta", "value": cursos, "url_name": "Inventario"})
        if has_feature(user, "ventas.ediciones"):
            chips.append({"label": "Ediciones abiertas", "value": ediciones, "url_name": "Ediciones"})
    elif contexto == "escolar":
        row = _fetch(
            """
            SELECT
              (SELECT COUNT(*) FROM cat_alumno WHERE estado = 'activo'),
              (SELECT COUNT(*) FROM tra_inscripcion),
              (SELECT COUNT(*) FROM cat_docente)
            """
        )
        alumnos, inscripciones, docentes = row or (0, 0, 0)
        if has_feature(user, "sii.alumnos") and scope_for(user, "sii.alumnos") != "own":
            chips.append({"label": "Alumnos activos", "value": alumnos, "url_name": "sii_alumnos"})
        if has_feature(user, "sii.inscripciones") and scope_for(user, "sii.inscripciones") != "own":
            chips.append({"label": "Inscripciones", "value": inscripciones, "url_name": "sii_inscripciones"})
        if has_feature(user, "sii.docentes"):
            chips.append({"label": "Docentes", "value": docentes, "url_name": "sii_docentes"})
    elif contexto == "docente":
        from api.inicio.widgets_docente import _curso_ids
        from ventas.models import EdicionCurso

        if has_feature(user, "aula.cursos"):
            ids = _curso_ids(user)
            grupos = EdicionCurso.objects.filter(
                id_curso__id_curso_id__in=ids,
                activo=True,
                estado="en_curso",
            ).count()
            chips.append({"label": "Mis grupos", "value": grupos, "url_name": "aula_dashboard"})
        if has_feature(user, "sii.alumnos"):
            chips.append(
                {"label": "Mis alumnos", "value": alumnos_visibles(user).count(), "url_name": "sii_alumnos"}
            )
    return chips

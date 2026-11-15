from api.inicio.cache import memo_user
from sii.identity import alumnos_visibles
from sii.models import Alumno, Docente, Inscripcion
from sii.rbac import has_feature, scope_for
from ventas.models import Cliente, EdicionCurso, Producto


def conteos_para(user, contexto):
    return memo_user(user, f"conteos:{contexto}", lambda: _conteos(user, contexto))


def _conteos(user, contexto):
    chips = []
    if contexto == "ventas":
        clientes = Cliente.objects.filter(activo=True).count()
        cursos = Producto.objects.filter(activo=True).count()
        ediciones = EdicionCurso.objects.filter(activo=True, estado__in=["programada", "en_curso"]).count()
        if has_feature(user, "ventas.clientes"):
            chips.append({"label": "Clientes activos", "value": clientes, "url_name": "Clientes"})
        if has_feature(user, "ventas.cursos"):
            chips.append({"label": "Cursos en venta", "value": cursos, "url_name": "Inventario"})
        if has_feature(user, "ventas.ediciones"):
            chips.append({"label": "Ediciones abiertas", "value": ediciones, "url_name": "Ediciones"})
    elif contexto == "escolar":
        alumnos = Alumno.objects.filter(estado="activo").count()
        inscripciones = Inscripcion.objects.count()
        docentes = Docente.objects.count()
        if has_feature(user, "sii.alumnos") and scope_for(user, "sii.alumnos") != "own":
            chips.append({"label": "Alumnos activos", "value": alumnos, "url_name": "sii_alumnos"})
        if has_feature(user, "sii.inscripciones") and scope_for(user, "sii.inscripciones") != "own":
            chips.append({"label": "Inscripciones", "value": inscripciones, "url_name": "sii_inscripciones"})
        if has_feature(user, "sii.docentes"):
            chips.append({"label": "Docentes", "value": docentes, "url_name": "sii_docentes"})
    elif contexto == "docente":
        from api.inicio.widgets_docente import _curso_ids

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

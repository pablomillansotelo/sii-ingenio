"""Accesos del hub de Control Escolar. Solo destinos reales o «Próximamente»."""

HUB_ACCESOS = [
    {"clave": "kardex", "label": "Kardex", "url_name": "campus_kardex", "icon": "bi-table", "estado": "listo"},
    {"clave": "estado_cuenta", "label": "Estado de cuenta", "url_name": "campus_estado_cuenta", "icon": "bi-wallet2", "estado": "listo"},
    {"clave": "ficha", "label": "Mi ficha", "url_name": "campus_ficha", "icon": "bi-person-vcard", "estado": "listo"},
    {"clave": "horario", "label": "Horario", "url_name": "sii_horario", "icon": "bi-clock", "estado": "listo"},
    {"clave": "constancias", "label": "Constancias", "url_name": "campus_constancias", "icon": "bi-file-earmark-text", "estado": "listo"},
    {"clave": "baja", "label": "Solicitud de baja", "url_name": "campus_bajas", "icon": "bi-x-circle", "estado": "listo"},
    {"clave": "expediente", "label": "Expediente digital", "url_name": "campus_expediente", "icon": "bi-folder", "estado": "listo"},
    {"clave": "credencial", "label": "Credencial", "url_name": "campus_credencial", "icon": "bi-person-badge", "estado": "listo"},
    {"clave": "aceptacion", "label": "Aceptación de materias", "url_name": "campus_aceptacion", "icon": "bi-check2-square", "estado": "listo"},
    {"clave": "normativa", "label": "Normativa", "url_name": "campus_normativa", "icon": "bi-book", "estado": "listo"},
    {"clave": "directorio", "label": "Directorio", "url_name": "campus_directorio", "icon": "bi-telephone", "estado": "listo"},
    {"clave": "mesa", "label": "Mesa de ayuda", "url_name": "campus_ayuda", "icon": "bi-life-preserver", "estado": "listo"},
    {"clave": "facturacion", "label": "Facturación", "url_name": "campus_facturacion", "icon": "bi-receipt", "estado": "listo"},
    {"clave": "ofertas", "label": "Cursos recomendados", "url_name": "campus_ofertas", "icon": "bi-stars", "estado": "listo"},
]

CLAVES_VALIDAS = {item["clave"] for item in HUB_ACCESOS}

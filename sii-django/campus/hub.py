"""Accesos del hub de Control Escolar. Solo destinos reales o «Próximamente»."""

HUB_ACCESOS = [
    {"clave": "kardex", "label": "Kardex", "url_name": "sii_kardex", "icon": "bi-table", "estado": "listo"},
    {"clave": "estado_cuenta", "label": "Estado de cuenta", "url_name": "mis_compras", "icon": "bi-wallet2", "estado": "listo"},
    {"clave": "ficha", "label": "Mi ficha", "url_name": "campus_ficha", "icon": "bi-person-vcard", "estado": "listo"},
    {"clave": "horario", "label": "Horario", "url_name": "sii_horario", "icon": "bi-clock", "estado": "listo"},
    {"clave": "constancias", "label": "Constancias", "url_name": None, "icon": "bi-file-earmark-text", "estado": "proximamente"},
    {"clave": "baja", "label": "Solicitud de baja", "url_name": None, "icon": "bi-x-circle", "estado": "proximamente"},
    {"clave": "expediente", "label": "Expediente digital", "url_name": None, "icon": "bi-folder", "estado": "proximamente"},
    {"clave": "credencial", "label": "Credencial", "url_name": None, "icon": "bi-person-badge", "estado": "proximamente"},
    {"clave": "aceptacion", "label": "Aceptación de materias", "url_name": None, "icon": "bi-check2-square", "estado": "proximamente"},
    {"clave": "normativa", "label": "Normativa", "url_name": None, "icon": "bi-book", "estado": "proximamente"},
    {"clave": "directorio", "label": "Directorio", "url_name": None, "icon": "bi-telephone", "estado": "proximamente"},
    {"clave": "mesa", "label": "Mesa de ayuda", "url_name": None, "icon": "bi-life-preserver", "estado": "proximamente"},
    {"clave": "facturacion", "label": "Facturación", "url_name": None, "icon": "bi-receipt", "estado": "proximamente"},
]

CLAVES_VALIDAS = {item["clave"] for item in HUB_ACCESOS}

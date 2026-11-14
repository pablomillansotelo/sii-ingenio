"""Documentos del expediente: prefix expediente/ (no mezclar con entregas/)."""

from django.core.exceptions import ValidationError

MAX_BYTES = 5 * 1024 * 1024
EXT_OK = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}
TIPOS_REQUERIDOS = ("identificacion", "domicilio", "certificado")


def validar_archivo(archivo):
    nombre = (getattr(archivo, "name", "") or "").lower()
    ext = ""
    if "." in nombre:
        ext = "." + nombre.rsplit(".", 1)[-1]
    if ext not in EXT_OK:
        raise ValidationError("Solo se aceptan PDF o imagen (JPG, PNG, WebP).")
    tam = getattr(archivo, "size", 0) or 0
    if tam > MAX_BYTES:
        raise ValidationError("El archivo no puede pesar más de 5 MB.")
    return archivo


def resumen_tipos(alumno):
    docs = list(alumno.documentos.all()) if alumno else []
    por_tipo = {}
    for doc in docs:
        por_tipo.setdefault(doc.tipo, []).append(doc)
    filas = []
    from sii.models import DocumentoExpediente

    for clave, etiqueta in DocumentoExpediente.TIPO_CHOICES:
        actuales = por_tipo.get(clave, [])
        vigente = actuales[0] if actuales else None
        estado = vigente.estado if vigente else "faltante"
        filas.append(
            {
                "tipo": clave,
                "etiqueta": etiqueta,
                "estado": estado,
                "documento": vigente,
                "historial": actuales,
            }
        )
    return filas

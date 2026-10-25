# Operación de Ventas y Aula

Manual corto para quien opera Ingenio día a día. El expediente escolar (altas, actas, horario, kardex) está en SII; esto cubre **cobro** y **la semana del grupo**.

## Ventas — call center

Rutas bajo `/ventas/`. El alumno no entra al POS: ve **Mis compras** (`/ventas/mis-compras/`).

| Qué | Dónde | Notas |
| :--- | :--- | :--- |
| Panel | `/ventas/` | Totales del mes y pendientes |
| Punto de venta | `/ventas/nueva/` | Un folio = un alumno. `cantidad > 1` reserva cupo, no clona inscripciones |
| Folios | `/ventas/folios/` | Abrir **Recibo** para el comprobante |
| Pagos | `/ventas/pagos/` | Caja: pendiente / parcial / pagado. La inscripción existe con folio pendiente; el aula no deja entregar hasta `pagado` |
| Clientes | `/ventas/clientes/` | El peek “ya inscrito” es solo lectura de SII |
| Recibo | `/ventas/recibos/<id>/` | HTML imprimible + **PDF**. Es comprobante interno, no CFDI |

Alta de vendedor: SII/admin crea la ficha. El POS ya no inventa un `Vendedor` al entrar.

## Aula — la semana del grupo

Rutas bajo `/aula/`. El **grupo** es la edición de ventas (`EdicionCurso`) ligada a `Inscripcion.id_edicion`. El docente ve las ediciones de los cursos que tiene en SII; el alumno solo las suyas.

| Qué | Dónde | Notas |
| :--- | :--- | :--- |
| Mis grupos | `/aula/` | Tarjetas por edición; cursos sin edición quedan aparte |
| Aula del grupo | `/aula/cursos/<curso>/g/<edicion>/` | Secciones + materiales + actividades + aviso + roster (docente) |
| Actividades | misma página / alta | Fecha límite y `cerrada` **bloquean** entregas |
| Materiales | sección → “Material” | Archivo, liga o texto/HTML corto |
| Aviso | `/aula/cursos/<curso>/g/<edicion>/aviso/` | Un recado, no un foro |
| Entregar | `/aula/actividades/<id>/entregar/` | Texto y/o archivo. En producción configura Blob o S3 |
| Calificar | `/aula/actividades/<id>/calificar/` | Solo inscritos de **esa** edición |
| Por calificar | `/aula/por-calificar/` y atajo en **Hoy** | Entregas sin nota del docente |
| Horario | se muestra en el curso; el dueño es SII (`/sii/horario/`) | |
| Kardex | `/sii/kardex/` | El aula escribe el promedio; SII exhibe |

Asignar docente se hace en `/sii/docentes/`. `/aula/cursos/<id>/asignar/` redirige ahí.

**Fuera de alcance:** foro entre alumnos, quiz, rúbricas, videollamada nativa.

## Archivos (entregas y materiales)

En Vercel el disco local **no persiste**. Orden de resolución:

1. `STORAGE_BACKEND=local|s3|vercel_blob` si está definido.
2. Si no: hay `BLOB_READ_WRITE_TOKEN` → Vercel Blob; si hay `AWS_STORAGE_BUCKET_NAME` → S3; si no → disco local (`MEDIA_ROOT`).
3. En `DEBUG=True`, S3/Blob sin credenciales caen a disco local.

Variables:

| Variable | Uso |
| :--- | :--- |
| `STORAGE_BACKEND` | `local`, `s3` o `vercel_blob` (opcional) |
| `BLOB_READ_WRITE_TOKEN` | Token de Vercel Blob (también `VERCEL_BLOB_READ_WRITE_TOKEN`) |
| `AWS_STORAGE_BUCKET_NAME` | Bucket S3 / R2 / MinIO |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Credenciales S3 |
| `AWS_S3_REGION_NAME` | Región |
| `AWS_S3_ENDPOINT_URL` | Endpoint compatible (R2, MinIO) |
| `AWS_S3_CUSTOM_DOMAIN` | CDN opcional |
| `AWS_QUERYSTRING_AUTH` | URLs firmadas (default true) |

## Cuentas

- Alta en SII de alumno/docente/vendedor: User + grupo y, si aplica, contraseña temporal una vez.
- Cliente creado desde Ventas: cuenta con contraseña inutilizable → “Olvidé mi contraseña” en `/cuenta/recuperar/`.
- Perfil y cambio de contraseña: `/cuenta/`.

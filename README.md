# SII Ingenio

**SII Ingenio** es la plataforma unificada de **Ingenio**: ventas del call center, control escolar (SII) y aula. Corre en un solo Django con un shell común, roles por módulo y PostgreSQL (negocio + autenticación).

## Qué ya está en producción

*   **Ventas:** panel, punto de venta con cupo por edición, clientes, folios, pagos, cursos, vendedores.
*   **SII:** alumnos, cursos, periodos, inscripciones, docentes, kardex, actas, horario y ficha.
*   **Aula:** actividades, entregas (texto o archivo), calificación masiva y aviso por calificar.
*   **Acceso:** login único, alta de cuenta al crear alumno/docente/vendedor, perfil y recuperación de contraseña.

## Qué falta (roadmap)

Prioridad alta:

1. **Pago en línea** — el cobro sigue siendo registro manual del call center.
2. **Documentación de operación** — Ventas y Aula aún no tienen un manual aparte del SII.
3. **PDF / CFDI** — el recibo es HTML imprimible.

Después:

*   Apps `docente/` y `administrador/` vacías (la lógica vive en `sii/` y `aula/`).
*   Storage persistente de archivos de entrega (hoy es disco local).
*   `/sii-sql` vacío; las migraciones de Django son la fuente de verdad.
*   Proyectos Vercel legacy `ventas-ingenio` y `aula-ingenio` (el unificado es `sii-ingenio` → `sii.modeloingenio.xyz`).

## Estructura

*   **`/sii-django`**: aplicación Django (configuración en `api/`), plantillas y estáticos.
*   **`/sii-sql`**: reservado para scripts SQL manuales.

### Tecnologías

*   Django 4.2 · PostgreSQL (Neon) · WhiteNoise · Vercel (`sii-django/vercel.json`)

Los estáticos de producción salen de `sii-django/staticfiles/` (`collectstatic` o `./build_files.sh`). Detalle en `sii-django/README.md` y `sii-django/docs/setup.md`.

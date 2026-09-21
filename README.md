# SII Ingenio

**SII Ingenio** es la plataforma unificada de **Ingenio**: ventas del call center, control escolar (SII) y aula. Corre en un solo Django con un shell común, roles por módulo y PostgreSQL (negocio + autenticación).

## Qué ya está en producción

*   **Ventas:** panel, punto de venta con cupo por edición, clientes, folios, pagos, cursos, vendedores.
*   **SII:** alumnos, cursos, periodos, inscripciones (alta, baja, reintento), docentes y asignaciones.
*   **Aula:** actividades, entregas, calificación y kardex.
*   **Acceso:** login único y módulos filtrados por rol (Administrador, Vendedor, Docente, Alumno).

## Qué falta (roadmap)

Prioridad alta:

1. **Cuentas al dar de alta** — crear alumno/docente no crea usuario de login; el vínculo es un `user_id` débil.
2. **Perfil** — `/cuenta/` solo muestra nombre y correo; no se edita ni se cambia contraseña.
3. **Actas** — la visión original incluye actas de calificaciones; hoy el kardex sale del promedio de actividades.
4. **Horario** — la ruta existe pero redirige al aula.
5. **Documentación** — `docs/` describe el SII viejo; no documenta Ventas ni Aula.

Después:

*   Pagos en línea (hoy el cobro es registro manual).
*   Adjuntos en tareas (la entrega es texto).
*   Apps `docente/` y `administrador/` vacías (la lógica vive en `sii/` y `aula/`).
*   `/sii-sql` vacío; las migraciones de Django son la fuente de verdad.
*   Proyectos Vercel legacy `ventas-ingenio` y `aula-ingenio` (el unificado es `sii-ingenio` → `sii.modeloingenio.xyz`).

## Estructura

*   **`/sii-django`**: aplicación Django (configuración en `api/`), plantillas y estáticos.
*   **`/sii-sql`**: reservado para scripts SQL manuales.

### Tecnologías

*   Django 4.2 · PostgreSQL (Neon) · WhiteNoise · Vercel (`sii-django/vercel.json`)

Los estáticos de producción salen de `sii-django/staticfiles/` (`collectstatic` o `./build_files.sh`). Detalle en `sii-django/README.md` y `sii-django/docs/setup.md`.

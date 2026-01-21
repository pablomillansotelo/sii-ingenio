# SII Ingenio

**SII Ingenio** es un Sistema Integral de Información (Student Information System) diseñado para la gestión académica y administrativa de instituciones educativas. Este sistema permite la administración de alumnos, docentes, cursos, inscripciones y calificaciones de manera centralizada.

## 🏢 Visión de Negocio

El objetivo principal de SII Ingenio es optimizar los procesos escolares mediante la digitalización de la información académica. El sistema está diseñado para manejar:

*   **Gestión de Alumnos:** Información personal, estatus (activo, graduado, etc.) y seguimiento académico.
*   **Gestión Académica:** Catálogos de cursos, periodos escolares y asignación de docentes.
*   **Procesos Administrativos:** Inscripciones, generación de actas y kardex de calificaciones.
*   **Seguridad:** Gestión de usuarios y roles diferenciados (Administrador, Docente, Alumno).

## 🛠 Vista Técnica General

El proyecto está estructurado como un monorepositorio que contiene los componentes necesarios para el despliegue de la aplicación.

### Estructura del Repositorio

*   **`/sii-django`**: Contiene el código fuente de la aplicación web construida con **Django**. Aquí reside toda la lógica de negocio, los modelos de datos, las vistas y la configuración del servidor.
*   **`/sii-sql`**: Contiene scripts SQL para la inicialización y mantenimiento de la base de datos (e.g., `init.sql`), útil para levantar el entorno o realizar migraciones manuales complejas.

### Tecnologías Clave

*   **Backend Framework:** Python / Django 4.1.3
*   **Base de Datos:** PostgreSQL. El sistema utiliza una arquitectura de base de datos múltiple para separar la autenticación (`auth`) de los datos del negocio (`default`).
*   **Servidor Web:** Gunicorn con Whitenoise para archivos estáticos.
*   **Infraestructura:** Preparado para despliegue containerizado (Docker friendly) y gestión de configuración mediante variables de entorno via `python-decouple`.

Para más detalles sobre cómo levantar el proyecto y la documentación técnica específica, por favor consulte el `README.md` dentro del directorio `sii-django`.

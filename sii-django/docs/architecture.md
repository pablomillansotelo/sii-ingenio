# Arquitectura del Proyecto

## Visión General

SII Ingenio utiliza una arquitectura monolítica basada en **Django**, servida a través de un servidor WSGI (**Gunicorn**) y utilizando **PostgreSQL** como motor de base de datos.

La característica más notable de la arquitectura es la separación de datos mediante el uso de múltiples bases de datos.

## Estrategia Multi-Base de Datos

Para mantener una separación clara entre los datos administrativos del framework (usuarios, permisos, sesiones) y los datos del negocio (alumnos, calificaciones), se implementó una estrategia de dos bases de datos.

### 1. Base de Datos `default` (Negocio)
Esta base de datos almacena toda la información relacionada con el dominio del sistema.

*   **Contenido:** Modelos definidos en las aplicaciones `sii`, `alumnos`, `docente`, etc.
*   **Tablas:** `cat_alumno`, `cat_curso`, `tra_inscripcion`, `cat_periodo`.
*   **Uso:** Operaciones diarias del sistema escolar.

### 2. Base de Datos `auth` (Autenticación)
Esta base de datos es gestionada casi exclusivamente por las aplicaciones internas de Django (`django.contrib.auth`, `django.contrib.sessions`, `django.contrib.admin`).

*   **Contenido:** Usuarios, Grupos, Permisos, Sesiones.
*   **Tablas:** `auth_user`, `django_session`, `auth_group`.
*   **Uso:** Login, Logout, validación de permisos.

## Database Router

La lógica para decidir en qué base de datos leer o escribir se encuentra centralizada en el `AuthRouter`.

*   **Ubicación:** `api/dbrouters/auth_router.py`
*   **Lógica:**
    *   Si el modelo pertenece a las apps `auth`, `contenttypes`, `sessions` o `admin`, la operación se dirige a la base de datos `auth`.
    *   Cualquier otro modelo (por defecto) se dirige a la base de datos `default`.
    *   Las relaciones (Foreign Keys) entre modelos de distintas bases de datos no están permitidas por defecto en Django, por lo que se deben manejar con cuidado (e.g., usando `user_id` entero en lugar de una FK directa a `User`, o gestionando la integridad manualmente).

### Ejemplo de Configuración (`settings.py`)

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        ...
    },
    'auth': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('AUTH_NAME'),
        ...
    },
}

DATABASE_ROUTERS = ['api.dbrouters.auth_router.AuthRouter']
```

## Estructura de Aplicaciones

El proyecto está dividido en aplicaciones Django para modularizar la funcionalidad:

| App | Propósito |
| :--- | :--- |
| **api** | Configuración global (settings, urls, wsgi). Actúa como el "proyecto" Django. |
| **sii** | Núcleo del negocio. Define los modelos base (`Alumno`, `Curso`) y lógica compartida. |
| **alumnos** | Portal del estudiante. Vistas para consultar calificaciones, kardex, etc. |
| **docente** | Portal del profesor. Gestión de grupos y captura de calificaciones. |
| **administrador** | Panel administrativo avanzado (fuera del admin de Django). |
| **usuario** | Gestión de perfiles y lógica común de usuarios (login/logout). |
| **ventas** | Dominio comercial (POS, folios, pagos, oferta). |
| **aula** | Operación didáctica (actividades, entregas, calificación). |

Roles, dueño de cada feature, matriz RBAC y roadmap: [roles-dominios-rbac.md](roles-dominios-rbac.md).

## Flujo de Petición (Request Lifecycle)

1.  **Nginx/Gunicorn** recibe la petición HTTP.
2.  **Django Middleware** procesa la seguridad, sesiones y autenticación (consultando la DB `auth`).
3.  **URL Dispatcher** (`api/urls.py`) enruta la petición a la vista correspondiente.
4.  **Vista** (e.g., `alumnos/views.py`) ejecuta la lógica de negocio.
    *   Consulta modelos de negocio (DB `default`).
    *   Prepara el contexto.
5.  **Template** Renderiza el HTML y lo devuelve al usuario.

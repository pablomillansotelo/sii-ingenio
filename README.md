# SII Ingenio

**SII Ingenio** es un Sistema Integral de Información (Student Information System) construido con **Django**, diseñado para la gestión académica y administrativa de instituciones educativas.

## 🏢 Visión de Negocio

El objetivo principal de SII Ingenio es optimizar los procesos escolares mediante la digitalización de la información académica. El sistema está diseñado para manejar:

*   **Gestión de Alumnos:** Información personal, estatus (activo, graduado, etc.) y seguimiento académico.
*   **Gestión Académica:** Catálogos de cursos, periodos escolares y asignación de docentes.
*   **Procesos Administrativos:** Inscripciones, generación de actas y kardex de calificaciones.
*   **Seguridad:** Gestión de usuarios y roles diferenciados (Administrador, Docente, Alumno).

## 🚀 Guía de Inicio Rápido

Sigue estos pasos para levantar el entorno de desarrollo local.

### Prerrequisitos

*   Python 3.8+
*   PostgreSQL (debes tener acceso para crear bases de datos)
*   Git

### Instalación

1.  **Crear y activar un entorno virtual:**

    ```bash
    # Linux/Mac
    python3 -m venv venv
    source venv/bin/activate

    # Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

2.  **Instalar dependencias:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuración de Variables de Entorno:**

    Crea un archivo `.env` en la raíz del proyecto basándote en la configuración de `api/settings.py`. Ejemplo:

    ```ini
    DEBUG=True
    SECRET_KEY=tu_clave_secreta_local

    # Base de datos de Negocio (Tablas del sistema)
    DB_NAME=sii_db
    DB_USER=postgres
    DB_PASSWORD=tu_password
    DB_HOST=localhost
    DB_PORT=5432

    # Base de datos de Autenticación (Usuarios Django)
    AUTH_NAME=sii_auth_db
    AUTH_USER=postgres
    AUTH_PASSWORD=tu_password
    AUTH_HOST=localhost
    AUTH_PORT=5432
    ```

4.  **Aplicar Migraciones:**

    ```bash
    python manage.py migrate
    python manage.py migrate --database=auth
    ```

5.  **Ejecutar el servidor:**

    ```bash
    python manage.py runserver
    ```

    Accede a `http://127.0.0.1:8000/`.

## 🛠 Estructura del Proyecto

*   **`api/`**: **Configuración del Proyecto**. Contiene `settings.py`, `urls.py` principal y la configuración WSGI/ASGI.
*   **`sii/`**: Aplicación "Core" del negocio.
*   **`alumnos/`, `docente/`, `administrador/`, `usuario/`**: Aplicaciones para cada rol o módulo funcional.
*   **`sql/`**: Scripts SQL auxiliares (e.g., `init.sql`) para mantenimiento manual de la base de datos.
*   **`docs/`**: Documentación detallada del proyecto (Arquitectura, Modelos, Setup avanzado).

## ⚙️ Características Técnicas Destacadas

### Multi-Database Architecture

El proyecto utiliza dos bases de datos:
1.  **Default**: Almacena la data del negocio (Alumnos, Cursos, Inscripciones).
2.  **Auth**: Almacena exclusivamente tablas de autenticación de Django (`auth_user`, `django_session`, etc.).

Esta separación se gestiona mediante un **Database Router** ubicado en `api/dbrouters/auth_router.py`.

### Documentación Adicional

Para detalles más profundos sobre arquitectura, modelos y guías avanzadas, revisa el directorio `/docs`.

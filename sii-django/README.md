# SII Django Backend

Este directorio contiene la aplicación backend construida con **Django**. Es el núcleo del sistema SII Ingenio, encargado de la lógica de negocio, interacción con la base de datos y renderizado de vistas.

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

    Crea un archivo `.env` en la raíz de `sii-django/` basándote en la configuración de `api/settings.py`. Ejemplo:

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

    > **Nota:** El sistema utiliza dos bases de datos separadas. Asegúrate de crear ambas en tu servidor PostgreSQL antes de correr migraciones.

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

    Antes de subir a Vercel, recolecta estáticos para que el logo y el JS del POS existan en producción:

    ```bash
    python manage.py collectstatic --noinput
    ```

## 📂 Estructura del Proyecto

El proyecto sigue una estructura modular de Django:

*   **`api/`**: **Directorio de Configuración del Proyecto**.
    *   Contiene `settings.py`, `urls.py` principal y la configuración WSGI/ASGI.
    *   **Nota importante:** A diferencia de la convención estándar donde la carpeta de configuración lleva el mismo nombre que el repositorio, aquí se llama `api`.
*   **`sii/`**: Aplicación "Core". Contiene modelos de negocio fundamentales (e.g., Catálogos, Tablas de configuración) y configuraciones generales.
*   **`alumnos/`**: Aplicación encargada de la lógica relacionada con los estudiantes (Kardex, Perfil, etc.).
*   **`docente/`**: Aplicación para la gestión y vistas de los profesores.
*   **`administrador/`**: Panel y lógica para administradores del sistema.
*   **`usuario/`**: Gestión de perfiles de usuario y autenticación común.
*   **`templates/`**: Plantillas HTML globales.
*   **`static/`**: Archivos estáticos de desarrollo (CSS, JS, logo).
*   **`staticfiles/`**: Salida de `collectstatic` que Vercel publica en `/static/`. Hay que regenerarla al agregar CSS, JS o imágenes (`python manage.py collectstatic --noinput` o `./build_files.sh`).

## ⚙️ Características Técnicas Destacadas

### Multi-Database Architecture

El proyecto está configurado para usar múltiples bases de datos:
1.  **Default**: Almacena la data del negocio (Alumnos, Cursos, Inscripciones).
2.  **Auth**: Almacena exclusivamente tablas de autenticación de Django (`auth_user`, `django_session`, etc.).

Esta separación se gestiona mediante un **Database Router** ubicado en `api/dbrouters/auth_router.py`.

### Documentación Adicional

Para detalles más profundos sobre arquitectura, modelos, roles/RBAC y guías avanzadas, revisa el directorio `/docs`.

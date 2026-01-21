# Guía de Instalación y Configuración

Esta guía detalla los pasos para configurar el entorno de desarrollo de SII Ingenio desde cero.

## 1. Requisitos del Sistema

*   **Sistema Operativo:** Linux, macOS o Windows (con WSL recomendado).
*   **Python:** Versión 3.8 o superior.
*   **PostgreSQL:** Versión 12 o superior.
*   **Git:** Para control de versiones.

## 2. Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd sii-ingenio/sii-django
```

## 3. Entorno Virtual

Es crucial usar un entorno virtual para aislar las dependencias del proyecto.

```bash
# Crear entorno virtual llamado 'venv'
python3 -m venv venv

# Activar entorno
# En macOS/Linux:
source venv/bin/activate
# En Windows:
.\venv\Scripts\activate
```

## 4. Instalación de Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Si encuentras errores con `psycopg2`, asegúrate de tener instaladas las librerías de desarrollo de PostgreSQL (`libpq-dev` en Linux).

## 5. Configuración de Base de Datos

El sistema requiere **dos** bases de datos. Debes crearlas manualmente en tu servidor PostgreSQL.

```sql
CREATE DATABASE sii_db;
CREATE DATABASE sii_auth_db;
```

## 6. Variables de Entorno (.env)

Crea un archivo llamado `.env` en la carpeta `sii-django/`. Copia y ajusta el siguiente contenido:

```ini
# Configuración General
DEBUG=True
SECRET_KEY=django-insecure-cambiar-esto-en-produccion
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de Datos de Negocio (sii_db)
DB_NAME=sii_db
DB_USER=postgres
DB_PASSWORD=tu_password_local
DB_HOST=localhost
DB_PORT=5432

# Base de Datos de Autenticación (sii_auth_db)
AUTH_NAME=sii_auth_db
AUTH_USER=postgres
AUTH_PASSWORD=tu_password_local
AUTH_HOST=localhost
AUTH_PORT=5432
```

## 7. Inicialización de la Base de Datos

### Migraciones

Django necesita crear las tablas en ambas bases de datos.

1.  **Migrar la base de datos de negocio (`default`):**
    ```bash
    python manage.py migrate
    ```

2.  **Migrar la base de datos de autenticación (`auth`):**
    ```bash
    python manage.py migrate --database=auth
    ```

### Crear Superusuario

Para acceder al panel de administración (`/admin`), necesitas un superusuario. Este se guardará en la base de datos `auth`.

```bash
python manage.py createsuperuser --database=auth
```
*Sigue las instrucciones en pantalla.*

## 8. Ejecución

```bash
python manage.py runserver
```

El servidor estará disponible en `http://127.0.0.1:8000`.

## Solución de Problemas Comunes

*   **Error `connection refused` a Postgres:** Verifica que `DB_HOST` y `DB_PORT` sean correctos y que el servicio de PostgreSQL esté corriendo.
*   **Error `relation "auth_user" does not exist`:** Asegúrate de haber corrido las migraciones para la base de datos `auth` explícitamente (`--database=auth`).
*   **Archivos estáticos no cargan:** Asegúrate de que `DEBUG=True` en tu `.env`. En producción, necesitarás correr `python manage.py collectstatic`.

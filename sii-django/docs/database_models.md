# Modelos de Datos

Este documento describe los principales modelos de datos del negocio utilizados en SII Ingenio. Estos modelos residen en la base de datos `default`.

## Convenciones

*   **Tablas de Catálogo:** Prefijo `cat_`. Representan datos maestros que cambian con poca frecuencia.
*   **Tablas Transaccionales:** Prefijo `tra_`. Representan operaciones del día a día (e.g., inscripciones).
*   **Gestión:** Todos los modelos tienen `managed = True`.

## Entidades Principales

### Alumno (`cat_alumno`)

Representa a un estudiante registrado en la institución.

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | AutoField | Llave primaria. |
| `user_id` | Integer | ID de referencia al usuario en la DB `auth`. No es una FK real a nivel de DB. |
| `nombre` | CharField(100) | Nombre(s) del alumno. |
| `apellido` | CharField(100) | Apellidos. |
| `curp` | CharField(18) | Identificador único (Clave Única de Registro de Población). |
| `email` | EmailField | Correo electrónico institucional/personal. |
| `fecha_nacimiento` | DateField | Fecha de nacimiento. |
| `estado` | CharField | Estatus actual: `activo`, `inactivo`, `graduado`, `cancelado`. |

### Curso (`cat_curso`)

Catálogo de materias o cursos disponibles.

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | AutoField | Llave primaria. |
| `nombre` | CharField(100) | Nombre del curso (e.g., "Matemáticas I"). |
| `descripcion` | TextField | Descripción detallada del contenido. |

### Periodo (`cat_periodo`)

Ciclos escolares.

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | AutoField | Llave primaria. |
| `nombre` | CharField(50) | Nombre del periodo (e.g., "2023-A"). |
| `fecha_inicio` | DateField | Inicio del ciclo. |
| `fecha_fin` | DateField | Fin del ciclo. |

### Inscripcion (`tra_inscripcion`)

Vincula a un alumno con un curso en un periodo específico.

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | AutoField | Llave primaria. |
| `alumno` | ForeignKey | Referencia a `cat_alumno`. |
| `curso` | ForeignKey | Referencia a `cat_curso`. |
| `periodo` | ForeignKey | Referencia a `cat_periodo`. |
| `fecha_inscripcion` | DateField | Fecha automática de creación. |
| `intento` | Integer | Número de vez que cursa la materia (default: 1). |
| `calificacion` | Decimal(5,2) | Nota final (0.00 - 100.00). Null si está en curso. |
| `estado` | CharField | `activo`, `inactivo`, `completado`, `cancelado`. |

## Notas sobre Relaciones

*   **Inscripción:** La combinación `alumno` + `curso` es única (`unique_together`), lo que implica que un alumno no puede tener dos inscripciones activas al mismo curso simultáneamente (aunque el modelo no restringe por periodo explícitamente en el unique, la lógica de negocio debería validarlo).
*   **Usuarios:** La relación entre `Alumno` y el sistema de autenticación es débil (`user_id`). Para obtener el objeto usuario, se utiliza el método `get_user()` del modelo `Alumno`, que consulta la base de datos `auth`.

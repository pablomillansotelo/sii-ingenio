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

Rutas bajo `/aula/`. El docente ve *sus* cursos; el alumno, los que puede cursar.

| Qué | Dónde | Notas |
| :--- | :--- | :--- |
| Mis cursos | `/aula/` | Lista filtrada por oficio |
| Actividades | `/aula/cursos/<id>/` | Alta, fecha límite (informativa), ponderación |
| Entregar | `/aula/actividades/<id>/entregar/` | Texto y/o archivo. El disco en Vercel es efímero |
| Calificar | `/aula/actividades/<id>/calificar/` | Individual o “Guardar todas” |
| Por calificar | `/aula/por-calificar/` | Escritorio del docente |
| Horario | se muestra en el curso; el dueño es SII (`/sii/horario/`) | |
| Kardex | `/sii/kardex/` | El aula escribe el promedio; SII exhibe. Un periodo cerrado o un acta publicada ya no se sobrescribe |

Asignar docente se hace en `/sii/docentes/`. `/aula/cursos/<id>/asignar/` redirige ahí.

## Cuentas

- Alta en SII de alumno/docente/vendedor: User + grupo y, si aplica, contraseña temporal una vez.
- Cliente creado desde Ventas: cuenta con contraseña inutilizable → “Olvidé mi contraseña” en `/cuenta/recuperar/`.
- Perfil y cambio de contraseña: `/cuenta/`.

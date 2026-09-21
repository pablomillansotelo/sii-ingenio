# Features faltantes por dominio

Inventario a partir de la repartición de `roles-dominios-rbac.md`. Pregunta: **si Ventas es dinero, SII expediente y Aula la semana del grupo, ¿qué pantallas o operaciones todavía no existen para que cada oficio cierre su ciclo?**

No es una lista de “cosas de un LMS/ERP genérico”. Cada renglón sale de un caso de uso que hoy se parte a la mitad o no tiene dueño.

Prioridad:

- **P0** — Sin esto el dominio no cierra su caso (hay que crearlo o recolocar lo que ya existe).
- **P1** — El oficio trabaja, pero a ciegas o con Excel.
- **P2** — Un ciclo escolar se puede vivir sin ello.
- **P3** — No construir hasta que un caso real lo pida.

Estado: `falta` (no hay modelo ni UI), `incompleto` (hay dato o pantalla a medias), `mal colgado` (existe en el dominio equivocado).

---

## Cómo se recorrió

Se caminó el ciclo completo de una persona en Ingenio:

1. El call center vende y cobra.
2. Control escolar deja el expediente en regla.
3. El docente opera el grupo.
4. El alumno estudia, consulta calificaciones y ve lo que pagó.

En cada paso se preguntó: **¿quién es dueño del dato?** y **¿hay pantalla con el alcance correcto?** Lo que sigue es el hueco, no el nice-to-have de mercado.

---

## Costura entre dominios (lo más caro si no se crea)

Estos no son “un módulo más”. Son features que **solo existen porque partimos el producto**. Si no se diseñan, Ventas, SII y Aula mienten entre sí.

| Feature | Dueño | Hoy | Pri | Qué rompe si no existe |
| :--- | :--- | :--- | :--- | :--- |
| **Edición comercial ↔ inscripción académica** | SII guarda el vínculo; Ventas reserva el cupo | La venta reserva `EdicionCurso`; la inscripción es `alumno+curso+periodo` y **no guarda la edición**. `unique_together (alumno, curso)` impide dos periodos como dos renglones. | **P0** | Cupo, grupo, docente y aula no coinciden. Dos ventas del mismo curso no se ven como reintento. El docente no sabe *qué* edición imparte. |
| **Política “¿puede entrar al aula si no pagó?”** | regla de negocio; SII/Aula la aplican leyendo Ventas | Al `inscribir_desde_venta` entra aunque `estado_pago=pendiente` | **P0** | El alumno cursa sin cobrar. Control escolar no tiene palanca. |
| **Cliente ↔ Alumno en actualizaciones** | Ventas escribe comercial; SII el expediente | Signal solo al *crear* cliente. Nombre/email/CURP se desincronizan. | **P0** | Mis compras no encuentra al alumno; kardex y recibo son “otra persona”. |
| **Baja SII → cupo / venta** | SII dispara; Ventas reacciona | `dar_baja` solo pone `cancelado`. No libera cupo ni cancela folio. | **P1** | Ediciones “llenas” con gente de baja. Dinero y expediente no cuadran. |
| **Calificación de aula → kardex oficial** | Aula calcula; **SII exhibe** | `actualizar_kardex` escribe `Inscripcion.calificacion` y un modelo `aula.Kardex` | **P0** (colgado) | El expediente oficial vive en la app del aula. Hay que mover consulta (y el modelo) a SII. |
| **Vendedor: ¿ya está inscrito?** | Ventas, lectura de SII | No hay badge ni ficha. El asesor abre otro sistema o nada. | **P1** | **Decidido: sí, solo lectura.** Hasta 0.5 el peek usa `Inscripcion` (curso catálogo + periodo). Luego, la edición ligada. |
| **Alumno: debo / ya pagué** | Ventas (mis compras) + aviso en Hoy | Banner de cobro solo para quien ya entra a Ventas (call center). El alumno no ve nada. | **P0** | **Decidido: mis compras muestra pendiente (y pagado).** |

Sin la costura **edición ↔ inscripción**, el resto del aula y del kardex se construye sobre un grupo fantasma.

---

## Ventas — “se vendió y se cobró”

Ciclo que debe cerrar el vendedor: prospecto → ficha → folio con cupo → cobro → comprobante. Ciclo del alumno: ver deuda, ver recibos.

### Ya cubre el oficio (no volver a inventarlas)

Panel, POS, folios, pagos, clientes, catálogo, ediciones, vendedores, descuento *por línea*, cupo, banner de pendientes para el asesor, estados de pago `pendiente/parcial/pagado`.

### Faltan

| Feature | Estado | Pri | Caso de uso | Notas de diseño |
| :--- | :--- | :--- | :--- | :--- |
| **Mis compras** | falta | **P0** | Alumno ve *sus* folios pendientes, parciales y pagados | Vista `own` por `id_alumno_sii` / email. Sin POS. El pendiente es visible a propósito. |
| **Recibo / comprobante** | falta | **P0** | Alumno o asesor imprime o guarda el folio | HTML imprimible basta; PDF después. No es factura fiscal. |
| **Detalle de folio** | incompleto | **P0** | Ver líneas, edición, pagos aplicados, no solo editar en modal | Hoy la fila no tiene expediente de la venta. El click del pendiente va a Pagos, el pagado no va a ningún detalle. |
| **Cancelar venta (flujo)** | incompleto | **P1** | Folio equivocado: libera cupo, no inscribe, deja rastro | Hay `estado=cancelada` y `DeleteVenta` (borra). Hace falta cancelar *con motivo*, no borrar historia. |
| **Ficha de cliente con estatus SII** | falta | **P1** | El asesor ve “alumno # / inscrito en X / pago” | **Decidido: lectura sí.** No es pantalla de control escolar. |
| **Plan de pagos / cuotas** | falta | **P1** | `parcial` existe; no hay calendario (enganche + fechas) | Sin esto el call center anota cuotas en observaciones. |
| **Corte de caja del día** | falta | **P1** | Cerrar el turno: cobrado, pendiente, por método | El panel tiene monto del mes, no el corte operativo. |
| **Comisiones liquidables** | incompleto | **P2** | `comision_pct` en vendedor; no hay reporte ni periodo de pago | Dato huérfano. |
| **Devolución / nota de crédito** | falta | **P2** | Cliente se baja o se equivocó el monto | Relacionado con baja SII. No reusar “eliminar pago” como devolución. |
| **Lista de espera** | falta | **P2** | Edición sin cupo: anotar y avisar | Hoy el POS bloquea. |
| **Bitácora de llamada** | falta | **P2** | Call center: último contacto, siguiente fecha | `notas` del cliente no es un historial. |
| **Cliente empresa (B2B)** | incompleto | **P2** | Campo `empresa`; no hay N alumnos bajo un pagador | Un folio con varias plazas (`cantidad`) no crea N inscripciones (el loop inscribe una vez por producto). **Bug de dominio:** `cantidad>1` no genera N alumnos. |
| **Descuentos con política** | incompleto | **P2** | Hoy es un número libre en el POS | Auditoría: quién autorizó 50 %. |
| **Factura CFDI** | falta | **P3** | Obligación fiscal MX si facturan | No bloquear el recibo interno. Dueño: Ventas, no SII. |
| **Pago en línea** | falta | **P3** | Alumno paga desde mis compras | Después del recibo; la caja del call center se queda. |
| **CRM / leads** | falta | **P3** | Prospecto que aún no es cliente | No es el caso actual del POS. |

**No es de Ventas:** kardex, listas de grupo, actividades, actas, horario oficial.

### Hueco oculto en lo que ya “funciona”

`inscribir_desde_venta` hace `get_or_create(alumno, curso)`. Segunda venta del mismo curso: el folio se cobra y **no pasa nada en SII**. Eso es feature faltante de costura, no un detalle del POS.

---

## SII — “el expediente es verdad”

Ciclo de control escolar: ficha de persona → periodo → inscripción en un **grupo** → (opcional) baja/reintento → kardex / acta. Ciclo del alumno: ver su ficha, su historial, su horario. Ciclo del docente: ver *su* lista oficial, no el LMS.

### Ya cubre el oficio (a medias)

Altas de alumno/curso/periodo/docente, inscripciones con baja y reintento, asignación docente-curso, kardex *como tabla* (en Aula).

### Faltan

| Feature | Estado | Pri | Caso de uso | Notas de diseño |
| :--- | :--- | :--- | :--- | :--- |
| **Kardex en SII** | mal colgado | **P0** | Consulta oficial alumno / docente / control | Mover ruta y menú. Modelo `Kardex` no debería vivir en `aula`. |
| **Grupo académico (= edición o sección)** | falta | **P0** | “Inglés 2026-A grupo mañana” con cupo, docente, lista | Hoy Curso es catálogo y Edición es de Ventas. SII inscribe al *catálogo*, no al grupo. Hay que nacer `Grupo`/`Seccion` en SII **o** colgar `Inscripcion.id_edicion` (con Periodo). Decisión de modelo, no cosmética. |
| **Inscripción por periodo (historial)** | incompleto | **P0** | Cursar otra vez en 2027 como renglón nuevo | `unique_together (alumno, curso)` + `reintentar()` muta el mismo row y borra calificación. El kardex pierde historia. |
| **Ficha de alumno (expediente)** | incompleto | **P0** | Ver una persona: estado, inscripciones, deudas (lectura), documentos | Hoy es renglón de tabla + modal. El alumno no tiene pantalla “mi ficha”. `Alumno` no trae teléfono ni dirección (están en Cliente). |
| **Lista oficial del grupo** | incompleto | **P0** | Pase de lista académico: inscritos activos de *este* curso-periodo | Inscripciones es un flat file de toda la escuela. El docente necesita “mi grupo”. |
| **Gate de pago → inscripción activa** | falta | **P0** | No dejar `activo` (o no abrir aula) si el folio está pendiente | Política explícita. Puede ser estado `inactivo` hasta pagado, o flag `puede_cursar`. |
| **Créditos / clave de materia** | falta | **P1** | Kardex institucional | La UI ya reserva columna `creditos` vacía. Falta en `Curso`. |
| **Calificación mínima / acreditado** | falta | **P1** | Acta: acreditó / no acreditó | Hoy hay un decimal o nada. |
| **Actas de calificación final** | falta | **P1** | Congelar la nota oficial del grupo-periodo | Dueño SII. **El docente publica** el acta final de *sus* grupos (eso deja constancia). **El cierre de periodo en SII congela** (nadie más edita). Control escolar ve todas. No hay actas de asistencia/conducta en este corte. |
| **Horario oficial** | falta | **P1** | Días y horas por grupo-periodo | SII es dueño. Aula solo lo muestra. El redirect `/alumnos/horario/` hoy va al dashboard del aula. |
| **Motivo y fecha de baja** | incompleto | **P1** | Auditoría académica | `dar_baja` no guarda por qué ni quién. |
| **Documentos del expediente** | falta | **P2** | CURP PDF, INE, certificado previo | Storage en SII, no en Aula. |
| **Constancia / historial PDF** | falta | **P2** | El alumno descarga constancia de estudios | Sale del kardex, no de Ventas. |
| **Contacto / tutor** | falta | **P2** | Menores o emergencia | No copiar el cliente: es dato escolar. |
| **Equivalencias / convalidación** | falta | **P3** | Materia cursada en otra institución | |
| **Graduación como flujo** | incompleto | **P3** | Estado `graduado` es un enum sin pantalla | |
| **Becas académicas** | falta | **P3** | Si la beca es de control escolar; si es descuento de precio, es Ventas | No duplicar. |

**No es de SII:** POS, caja, publicar tarea, calificar actividad (eso alimenta el kardex, no lo exhibe).

### Ficha `Alumno` demasiado flaca

Para ser dueño del expediente, SII debería poder contactar y ubicar al estudiante **sin abrir Ventas**. Mínimo P1: teléfono, y un vínculo explícito y estable al cliente (ya hay FK al revés). Si no, control escolar sigue dependiendo del call center para un dato que es de la persona, no de la venta.

---

## Aula — “qué pasa esta semana en el grupo”

Ciclo del docente: abrir *su* grupo → ver lista → publicar trabajo → recibir → calificar → (el promedio se va a SII). Ciclo del alumno: entrar al curso, ver material, entregar, ver retro.

Hoy el aula es **solo una lista de actividades**. Eso no es un aula; es un buzón de tareas.

### Ya cubre

Alta/edición de actividad (nombre, ponderación, tipo, fecha límite), entrega en texto, calificación con comentario, promedio ponderado hacia inscripción.

### Faltan

| Feature | Estado | Pri | Caso de uso | Notas de diseño |
| :--- | :--- | :--- | :--- | :--- |
| **Roster del curso** | falta | **P0** | El docente ve a quién le imparte, no solo tareas | Debe leer inscripciones *del grupo*, no el catálogo `Curso` suelto. Depende de la costura edición/grupo. |
| **Materiales / recursos** | falta | **P0** | Subir PDF, liga, video. Sin esto el alumno no “tiene clase” en la plataforma | Dueño Aula. No es el expediente SII. |
| **Forzar fecha límite** | incompleto | **P1** | `estado=cerrada` no impide entregar; no hay corte automático | |
| **Entrega con archivo** | falta | **P1** | Tarea que no cabe en un textarea | Storage. |
| **Tablero / aviso del grupo** | falta | **P1** | “El sábado no hay clase” | Un recado, no un foro. |
| **Por calificar (Hoy del docente)** | falta | **P1** | Escritorio: N entregas sin nota | Feature de Hoy, datos de Aula. |
| **Rúbrica o desglose** | falta | **P2** | Examen con varios criterios | Un decimal basta el primer ciclo. |
| **Reabrir entrega / intento extra** | falta | **P2** | El maestro permite fuera de tiempo | |
| **Asistencia diaria** | falta | **P2** | Pase de lista en clase | Toma: Aula. Oficio/acta: SII. No hacer dos padrones. |
| **Unidades / temario** | falta | **P2** | Ordenar actividades | |
| **Foro / comentarios entre alumnos** | falta | **P3** | | |
| **Videollamada integrada** | falta | **P3** | Un campo URL en el grupo basta si se necesita | |
| **Asignar docente desde el curso** | mal colgado | **P2** | Ya está en SII Docentes | Dejar de duplicar o hacerlo alias. |

**No es de Aula:** kardex de consulta, recibos, plantilla, periodos, cupo.

---

## Transversal (ningún dominio, todos los logins)

| Feature | Estado | Pri | Caso de uso |
| :--- | :--- | :--- | :--- |
| **Invitación / primer acceso** | incompleto | **P0** | Alumno y docente existen como ficha; el `User` del alumno se crea con password aleatorio **que nadie ve** | Sin esto RBAC de alumno es teatro: no pueden entrar. |
| **Login de docente al alta** | falta | **P0** | Mismo problema; ni siquiera hay signal de User para docente | |
| **Reset de contraseña** | falta | **P0** | Login no ofrece “olvidé mi password” | |
| **Perfil editable** | incompleto | **P1** | `/cuenta/` es de solo lectura | |
| **Cambio de contraseña autenticado** | falta | **P1** | | |
| **Auditoría** | falta | **P1** | Quién dio de baja, quién descontó, quién canceló folio | Tabla de eventos, no Django Admin. |
| **Avisos por correo** | falta | **P2** | Recibo, “te calificaron”, “actividad nueva”, “pago pendiente” | |
| **Hoy por oficio** | incompleto | **P1** | Hoy está pensado para call center | Alumno: deuda + próximas entregas. Docente: por calificar. Control: bajas / actas abiertas. |

---

## Mapa compacto: crear vs recolocar vs no hacer

### Hay que **crear** (no existe)

P0: mis compras, recibo, detalle de folio, grupo/edición en la inscripción, historial de inscripción por periodo, ficha de alumno, roster de grupo, materiales de aula, gate de pago, invitación/password, reset.

P1: cancelación con motivo, cuotas, corte de caja, estatus SII en ficha de cliente, actas, horario, créditos y acreditación, fecha límite real, entrega archivo, aviso de grupo, Hoy del docente, teléfono en expediente, motivo de baja, auditoría, perfil.

### Hay que **recolocar** (existe en el lugar equivocado)

- Kardex: Aula → SII.
- Asignar docente en el curso de Aula → SII (o alias).
- Horario: redirect a Aula → SII.
- Modelo `aula.Kardex` → paquete SII cuando se mueva la consulta.

### Hay que **arreglar como feature de costura** (el código hace otra cosa)

- `cantidad` en el POS no inscribe N personas.
- Segunda venta del mismo curso no reintenta ni avisa.
- Baja no libera cupo.
- Inscripción al vender aunque no haya pagado.
- Signal de cliente solo en create.

### **No construir** todavía (P3)

CFDI, pasarela, CRM, lista de espera sofisticada, foro, videollamada nativa, equivalencias, flujo de graduación, becas (hasta decidir si son precio o expediente).

---

## Qué implica para el roadmap anterior

El documento de RBAC ordenaba: candado → kardex a SII → mis compras → identidad → actas/horario → archivos de aula → pago en línea.

Tras este inventario, **se inserta un corte de modelo antes de pintar más pantallas de alumno**:

1. **Fase 0** — RBAC (catálogo, unión de grupos, candado por feature, placeholder mis compras). **Hecha en código.**
2. **Fase 0.5 — Costura de grupo** — `Inscripcion` ligada a edición/grupo; historial por periodo; gate de pago; sync cliente-alumno. Si no, mis compras y el aula mienten. El peek de inscripción sigue el mismo vínculo.
3. **Fase 1** — Kardex a SII + ficha + lista de grupo (ya con el vínculo correcto).
4. **Fase 2** — Mis compras (UI completa: pendiente + pagado) + recibo + detalle de folio + peek de inscripción en ficha cliente.
5. **Fase 3** — Identidad usable (invitación, reset). Sin esto nadie prueba 1–2 como alumno de verdad. La unión vendedor+docente ya vive en Fase 0.
6. **Fase 4** — Aula usable: materiales, roster, fecha límite, archivos.
7. **Fase 5** — Actas de calificación final (docente en sus grupos), horario, créditos, cuotas, corte de caja, cancelación con motivo.
8. **Fase 6** — Pago en línea, CFDI, el resto P3.

Las fases 4 y 5 del RBAC original se parten: **aula operativa** no debe esperar a las actas, y **actas** no deben bloquear materiales.

---

## Criterio para no inflar el backlog

Si un pedido no tiene dueño en Ventas / SII / Aula, o duplica un dato que ya vive en otro dominio (precio en SII, kardex en Aula, cupo en inscripción sin edición), **no es feature nueva: es una violación de la repartición**. Primero se reubica; luego se crea.

let carrito = [];

function edicionesPos() {
  const node = document.getElementById("ediciones-pos");
  if (!node) return [];
  try {
    return JSON.parse(node.textContent);
  } catch (err) {
    return [];
  }
}

function filtrarEdicionesPorCurso() {
  const cursoId = document.getElementById("id_producto_add").value;
  const select = document.getElementById("id_edicion_add");
  if (!select) return;
  const actuales = edicionesPos().filter((item) => String(item.curso_id) === String(cursoId));
  const valor = select.value;
  select.innerHTML = '<option value="">Sin edición</option>';
  actuales.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = item.label;
    if (item.cupo <= 0) option.disabled = true;
    select.appendChild(option);
  });
  if ([...select.options].some((opt) => opt.value === valor)) {
    select.value = valor;
  }
}

function agregarProducto() {
  const select = document.getElementById("id_producto_add");
  const edicionSelect = document.getElementById("id_edicion_add");
  const idProducto = select.value;
  const nombreProducto = select.selectedOptions[0] ? select.selectedOptions[0].text : "";
  const idEdicion = edicionSelect.value;
  const nombreEdicion = idEdicion && edicionSelect.selectedOptions[0]
    ? edicionSelect.selectedOptions[0].text
    : "";
  const cantidad = document.getElementById("cantidad_add").value;
  const descuento = document.getElementById("descuento_add").value || "0";
  const abiertas = edicionesPos().filter((item) => String(item.curso_id) === String(idProducto));
  if (!idProducto || !cantidad) {
    alert("Selecciona curso y plazas");
    return;
  }
  if (abiertas.length && !idEdicion) {
    alert("Este curso tiene ediciones abiertas: elige una para reservar cupo.");
    return;
  }
  carrito.push({
    id_producto: idProducto,
    nombre_producto: nombreProducto,
    id_edicion: idEdicion,
    nombre_edicion: nombreEdicion,
    cantidad,
    descuento,
  });
  renderCarrito();
  select.selectedIndex = 0;
  filtrarEdicionesPorCurso();
  document.getElementById("cantidad_add").value = "1";
  document.getElementById("descuento_add").value = "";
}

function renderCarrito() {
  const tbody = document.querySelector("#tblProducts tbody");
  if (!carrito.length) {
    tbody.innerHTML = '<tr><td colspan="4"><div class="empty-state text-center text-muted py-4 px-3"><p class="mb-0">El carrito está vacío. Agrega un curso en el paso 2.</p></div></td></tr>';
    return;
  }
  tbody.innerHTML = carrito.map((item, idx) => `
    <tr>
      <td>${item.nombre_producto}${item.nombre_edicion ? `<div class="small text-muted">${item.nombre_edicion}</div>` : ""}</td>
      <td>${item.cantidad}</td>
      <td>${item.descuento || "—"}</td>
      <td><button type="button" class="btn btn-outline-secondary btn-sm" onclick="eliminarProducto(${idx})">Quitar</button></td>
    </tr>`).join("");
}

function eliminarProducto(idx) {
  carrito.splice(idx, 1);
  renderCarrito();
}

function pagar_carrito() {
  const idCliente = document.getElementById("id_cliente_add").value;
  const fecha = document.getElementById("fecha_add").value;
  const observaciones = (document.getElementById("observaciones_add") || {}).value || "";
  if (!idCliente || !fecha || carrito.length === 0) {
    alert("Selecciona cliente, fecha y al menos un curso.");
    return;
  }
  const cfg = window.INGENIO_POS || {};
  const form = document.createElement("form");
  form.method = "POST";
  form.action = cfg.addUrl || "";
  form.innerHTML = `<input type="hidden" name="csrfmiddlewaretoken" value="${cfg.csrf || ""}">
    <input type="hidden" name="id_cliente_add" value="${idCliente}">
    <input type="hidden" name="fecha_add" value="${fecha}">
    <input type="hidden" name="observaciones_add" value="${observaciones.replace(/"/g, "&quot;")}">`;
  carrito.forEach((item) => {
    const edicion = item.id_edicion || "";
    form.innerHTML += `<input type="hidden" name="nplainArray[]" value="${item.id_producto},${edicion},${item.cantidad},${item.descuento}">`;
  });
  document.body.appendChild(form);
  form.submit();
}

document.addEventListener("DOMContentLoaded", () => {
  const select = document.getElementById("id_producto_add");
  if (select) {
    select.addEventListener("change", filtrarEdicionesPorCurso);
    filtrarEdicionesPorCurso();
  }
  const cliente = document.getElementById("id_cliente_add");
  if (cliente) {
    cliente.addEventListener("change", mostrarPeekInscripcion);
    mostrarPeekInscripcion();
  }
});

function inscripcionesPeek() {
  const node = document.getElementById("inscripciones-peek");
  if (!node) return {};
  try {
    return JSON.parse(node.textContent);
  } catch (err) {
    return {};
  }
}

function mostrarPeekInscripcion() {
  const caja = document.getElementById("pos-inscripcion-peek");
  const select = document.getElementById("id_cliente_add");
  if (!caja || !select) return;
  const filas = inscripcionesPeek()[String(select.value)] || [];
  if (!filas.length) {
    caja.classList.add("d-none");
    caja.textContent = "";
    return;
  }
  caja.classList.remove("d-none");
  caja.innerHTML = "<strong>Ya inscrito:</strong> " + filas.map((fila) => {
    const extra = fila.edicion ? ` · ${fila.edicion}` : "";
    return `${fila.curso}${extra} (${fila.periodo})`;
  }).join("; ");
}

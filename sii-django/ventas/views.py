from datetime import date

from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Count
from .models import Cliente, Producto, Venta, VentaDetalle, Vendedor, EdicionCurso, Pago
from .forms import (
    AddClienteForm,
    EditarClienteForm,
    AddProductoForm,
    EditarProductoForm,
    EditarVentaForm,
    AddVentaForm,
    AddVentaDetalleForm,
    AddVendedorForm,
    EditarVendedorForm,
    AddEdicionForm,
    EditarEdicionForm,
    AddPagoForm,
    EditarPagoForm,
)
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required

from .services import inscribir_desde_venta


def _vendedor_actual(request):
    return Vendedor.obtener_o_crear_desde_usuario(request.user)


def _parse_carrito_item(item):
    partes = [p.strip() for p in item.split(",")]
    if len(partes) == 3:
        return partes[0], None, partes[1], partes[2]
    if len(partes) >= 4:
        return partes[0], partes[1] or None, partes[2], partes[3]
    raise ValueError("Formato de carrito inválido")


# Create your views here.
@login_required
def dashboard_view(request):
    hoy = timezone.localdate()
    inicio_mes = hoy.replace(day=1)
    ventas_mes = Venta.objects.filter(fecha__gte=inicio_mes, estado="confirmada").prefetch_related(
        "ventadetalle_set"
    )
    monto_mes = sum(venta.monto for venta in ventas_mes)
    return render(
        request,
        "ventas/dashboard.html",
        {
            "stats": [
                {"label": "Clientes activos", "value": Cliente.objects.filter(activo=True).count(), "href": "Clientes"},
                {"label": "Cursos activos", "value": Producto.objects.filter(activo=True).count(), "href": "Inventario"},
                {
                    "label": "Ediciones abiertas",
                    "value": EdicionCurso.objects.filter(
                        activo=True, estado__in=EdicionCurso.ESTADOS_ABIERTOS
                    ).count(),
                    "href": "Ediciones",
                },
                {"label": "Ventas del mes", "value": ventas_mes.count(), "href": "Ventas"},
                {"label": "Monto del mes", "value": f"${monto_mes:,.0f}", "href": "Ventas"},
                {
                    "label": "Pagos pendientes",
                    "value": Venta.objects.filter(estado_pago="pendiente").count(),
                    "href": "Pagos",
                },
            ],
            "ultimas_ventas": Venta.objects.select_related("id_cliente", "id_vendedor").order_by("-id_venta")[:8],
        },
    )


@login_required
def carrito_view(request):
    context = {
        "form_venta": AddVentaForm(),
        "form_add_venta_detalle": AddVentaDetalleForm(),
        "vendedor": _vendedor_actual(request),
        "ediciones_pos": [
            {
                "id": edicion.pk,
                "curso_id": edicion.id_curso_id,
                "label": f"{edicion.codigo_edicion} · {edicion.cupo_disponible} lugares",
                "cupo": edicion.cupo_disponible,
            }
            for edicion in EdicionCurso.objects.filter(
                activo=True, estado__in=EdicionCurso.ESTADOS_ABIERTOS
            ).order_by("codigo_edicion")
        ],
    }
    return render(request, "ventas/carrito.html", context)


@login_required
def add_carrito_view(request):
    if request.method != "POST":
        return redirect("Carrito")

    id_cliente_add = request.POST.get("id_cliente_add")
    fecha_add = request.POST.get("fecha_add")
    observaciones = request.POST.get("observaciones_add", "")
    nplainArray = request.POST.getlist("nplainArray[]")

    try:
        cliente = Cliente.objects.get(pk=id_cliente_add, activo=True)
    except Cliente.DoesNotExist:
        messages.error(request, "Cliente no encontrado")
        return redirect("Carrito")

    if not nplainArray:
        messages.error(request, "Agrega al menos un curso al carrito")
        return redirect("Carrito")

    vendedor = _vendedor_actual(request)

    try:
        with transaction.atomic():
            venta = Venta.objects.create(
                id_cliente=cliente,
                id_vendedor=vendedor,
                fecha=date.fromisoformat(fecha_add) if fecha_add else timezone.localdate(),
                observaciones=observaciones or "",
                estado=Venta.ESTADO_CONFIRMADA,
                estado_pago=Venta.PAGO_PENDIENTE,
            )

            for item in nplainArray:
                id_producto, id_edicion, cantidad_str, descuento_str = _parse_carrito_item(item)
                cantidad = int(cantidad_str)
                if cantidad <= 0:
                    raise ValueError("La cantidad debe ser mayor a cero")
                producto = Producto.objects.get(pk=id_producto, activo=True)
                edicion = None
                abiertas = producto.ediciones.filter(
                    activo=True, estado__in=EdicionCurso.ESTADOS_ABIERTOS
                )
                if id_edicion:
                    edicion = EdicionCurso.objects.select_for_update().get(
                        pk=id_edicion, activo=True, id_curso=producto
                    )
                    edicion.reservar_cupo(cantidad)
                elif abiertas.exists():
                    raise ValueError(f"Selecciona una edición para {producto.producto}")

                descuento = None
                if descuento_str not in (None, ""):
                    descuento = float(descuento_str)
                    if descuento < 0:
                        descuento = 0

                precio = edicion.precio_aplicable if edicion else producto.precio_unitario
                VentaDetalle.objects.create(
                    id_venta=venta,
                    id_producto=producto,
                    id_edicion=edicion,
                    cantidad=cantidad,
                    descuento=descuento,
                    precio_unitario=precio,
                )

            inscripciones = inscribir_desde_venta(venta)
    except (Producto.DoesNotExist, EdicionCurso.DoesNotExist):
        messages.error(request, "Uno de los cursos o ediciones no está disponible")
        return redirect("Carrito")
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("Carrito")

    extra = f" Se generaron {inscripciones} inscripción(es) en el SII." if inscripciones else ""
    messages.success(request, f"Venta {venta.folio} confirmada.{extra}")
    return redirect("Ventas")

@login_required
def ventas_view(request):
    ventas = Venta.objects.select_related("id_cliente", "id_vendedor").prefetch_related(
        "ventadetalle_set__id_producto", "ventadetalle_set__id_edicion"
    ).order_by("-id_venta")
    form_editar_venta = EditarVentaForm()
    context = {
        'Ventas': ventas,
        'form_editar_venta': form_editar_venta,
    }
    return render(request, 'ventas/ventas.html', context)

@login_required
def edit_venta_view(request):
    if request.method == "POST":
        venta_id = request.POST.get("id_venta") or request.POST.get("id_venta_editar")
        if venta_id:
            try:
                venta = Venta.objects.get(pk=venta_id)
                cliente_id = request.POST.get("id_cliente")
                if cliente_id:
                    venta.id_cliente = Cliente.objects.get(pk=cliente_id)
                if request.POST.get("fecha"):
                    venta.fecha = request.POST.get("fecha")
                if "folio" in request.POST:
                    venta.folio = request.POST.get("folio") or venta.folio
                if request.POST.get("estado"):
                    venta.estado = request.POST.get("estado")
                if request.POST.get("estado_pago"):
                    venta.estado_pago = request.POST.get("estado_pago")
                if "observaciones" in request.POST:
                    venta.observaciones = request.POST.get("observaciones") or ""
                venta.save()
                if venta.estado == "confirmada":
                    inscribir_desde_venta(venta)
                messages.success(request, "La venta ha sido modificada")
            except (Venta.DoesNotExist, Cliente.DoesNotExist):
                messages.error(request, "Venta o cliente no encontrado")
    return redirect("Ventas")

@login_required
def clientes_view(request):
    clientes = Cliente.objects.all()
    form_cliente = AddClienteForm()
    form_editar_cliente = EditarClienteForm()
    context = {
        'Clientes': clientes,
        'form_cliente': form_cliente,
        'form_editar_cliente': form_editar_cliente,
    }
    return render(request, 'ventas/clientes.html', context)

@login_required
def add_clientes_view(request):
    if request.method == "POST":
        nombre = request.POST.get('nombre')
        apellidos = request.POST.get('apellidos')
        direccion = request.POST.get('direccion')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        if nombre and apellidos and direccion and email:
            activo = request.POST.get("activo") in ("on", "true", "True", "1")
            Cliente.objects.create(
                nombre=nombre,
                apellidos=apellidos,
                direccion=direccion,
                email=email,
                telefono=telefono or None,
                curp=request.POST.get("curp") or None,
                empresa=request.POST.get("empresa") or None,
                notas=request.POST.get("notas") or "",
                activo=activo if request.POST.get("activo") is not None else True,
            )
            messages.success(request, 'El cliente ha sido agregado')
    return redirect('Clientes')

@login_required
def edit_clientes_view(request):
    if request.method == "POST":
        cliente_id = request.POST.get('id_personal_editar')
        if cliente_id:
            try:
                cliente = Cliente.objects.get(pk=cliente_id)
                cliente.nombre = request.POST.get("nombre", cliente.nombre)
                cliente.apellidos = request.POST.get("apellidos", cliente.apellidos)
                cliente.direccion = request.POST.get("direccion", cliente.direccion)
                cliente.email = request.POST.get("email", cliente.email)
                cliente.telefono = request.POST.get("telefono", cliente.telefono)
                cliente.curp = request.POST.get("curp") or None
                cliente.empresa = request.POST.get("empresa") or None
                cliente.notas = request.POST.get("notas") or ""
                cliente.activo = request.POST.get("activo") in ("on", "true", "True", "1")
                cliente.save()
                messages.success(request, "El cliente ha sido modificado")
            except Cliente.DoesNotExist:
                messages.error(request, 'Cliente no encontrado')
    return redirect('Clientes')

@login_required
def delete_clientes_view(request):
    if request.method == "POST":
        cliente_id = request.POST.get('id_personal_eliminar')
        if cliente_id:
            try:
                cliente = Cliente.objects.get(pk=cliente_id)
                # Verificar si tiene ventas asociadas
                if Venta.objects.filter(id_cliente=cliente).exists():
                    messages.error(request, 'No se puede eliminar el cliente porque tiene ventas asociadas')
                else:
                    cliente.delete()
                    messages.success(request, 'El cliente ha sido eliminado')
            except Cliente.DoesNotExist:
                messages.error(request, 'Cliente no encontrado')
    return redirect('Clientes')

@login_required
def inventario_view(request):
    productos = Producto.objects.select_related("id_curso").all()
    form_producto = AddProductoForm()
    form_editar_producto = EditarProductoForm()
    context = {
        'Productos': productos,
        'form_producto': form_producto,
        'form_editar_producto': form_editar_producto,
    }
    return render(request, 'ventas/inventario.html', context)

@login_required
def add_producto_view(request):
    if request.method == "POST":
        producto = request.POST.get('producto')
        precio_unitario = request.POST.get('precio_unitario')
        if producto and precio_unitario:
            Producto.objects.create(
                producto=producto,
                precio_unitario=precio_unitario,
                codigo=request.POST.get("codigo") or None,
                descripcion=request.POST.get("descripcion") or "",
                duracion_horas=request.POST.get("duracion_horas") or None,
                modalidad=request.POST.get("modalidad") or "online",
                activo=request.POST.get("activo", "on") in ("on", "true", "True", "1"),
            )
            messages.success(request, 'El producto ha sido agregado')
    return redirect('Inventario')

@login_required
def delete_producto_view(request):
    if request.method == "POST":
        producto_id = request.POST.get('id_producto_eliminar')
        if producto_id:
            try:
                producto = Producto.objects.get(pk=producto_id)
                # Verificar si está en ventas
                if VentaDetalle.objects.filter(id_producto=producto).exists():
                    messages.error(request, 'No se puede eliminar el producto porque está en ventas')
                else:
                    producto.delete()
                    messages.success(request, 'El producto ha sido eliminado')
            except Producto.DoesNotExist:
                messages.error(request, 'Producto no encontrado')
    return redirect('Inventario')

@login_required
def edit_producto_view(request):
    if request.method == "POST":
        producto_id = request.POST.get('id_producto_editar')
        if producto_id:
            try:
                producto = Producto.objects.get(pk=producto_id)
                producto.producto = request.POST.get("producto", producto.producto)
                precio = request.POST.get("precio_unitario")
                if precio:
                    try:
                        producto.precio_unitario = float(precio)
                    except ValueError:
                        messages.error(request, "Precio inválido")
                        return redirect("Inventario")
                if "codigo" in request.POST:
                    producto.codigo = request.POST.get("codigo") or None
                if "descripcion" in request.POST:
                    producto.descripcion = request.POST.get("descripcion") or ""
                if request.POST.get("duracion_horas") not in (None, ""):
                    producto.duracion_horas = request.POST.get("duracion_horas")
                if request.POST.get("modalidad"):
                    producto.modalidad = request.POST.get("modalidad")
                producto.activo = request.POST.get("activo") in ("on", "true", "True", "1")
                producto.save()
                messages.success(request, 'El producto ha sido modificado')
            except Producto.DoesNotExist:
                messages.error(request, 'Producto no encontrado')
    return redirect('Inventario')

@login_required
def delete_venta_view(request):
    if request.method == "POST":
        venta_id = request.POST.get('id_venta_eliminar')
        if venta_id:
            try:
                venta = Venta.objects.select_related().prefetch_related(
                    "ventadetalle_set__id_edicion"
                ).get(pk=venta_id)
                with transaction.atomic():
                    for det in venta.ventadetalle_set.select_related("id_edicion"):
                        if det.id_edicion_id:
                            edicion = EdicionCurso.objects.select_for_update().get(pk=det.id_edicion_id)
                            edicion.liberar_cupo(det.cantidad)
                    VentaDetalle.objects.filter(id_venta=venta).delete()
                    venta.delete()
                messages.success(request, "La venta y su contenido se ha eliminado")
            except Venta.DoesNotExist:
                messages.error(request, 'Venta no encontrada')
    return redirect('Ventas')


@login_required
def vendedores_view(request):
    return render(
        request,
        "ventas/vendedores.html",
        {
            "Vendedores": Vendedor.objects.annotate(num_ventas=Count("ventas")).order_by("nombre"),
            "form_vendedor": AddVendedorForm(),
            "form_editar_vendedor": EditarVendedorForm(),
        },
    )


@login_required
def add_vendedor_view(request):
    if request.method == "POST":
        form = AddVendedorForm(request.POST)
        if form.is_valid():
            vendedor = form.save(commit=False)
            vendedor.user_id = request.user.pk
            vendedor.save()
            messages.success(request, "Vendedor registrado")
        else:
            messages.error(request, "Revisa los datos del vendedor")
    return redirect("Vendedores")


@login_required
def edit_vendedor_view(request):
    if request.method == "POST":
        vendedor_id = request.POST.get("id_vendedor") or request.POST.get("id_vendedor_editar")
        try:
            vendedor = Vendedor.objects.get(pk=vendedor_id)
            form = EditarVendedorForm(request.POST, instance=vendedor)
            if form.is_valid():
                form.save()
                messages.success(request, "Vendedor actualizado")
            else:
                messages.error(request, "Revisa los datos del vendedor")
        except (Vendedor.DoesNotExist, ValueError, TypeError):
            messages.error(request, "Vendedor no encontrado")
    return redirect("Vendedores")


@login_required
def delete_vendedor_view(request):
    if request.method == "POST":
        try:
            vendedor = Vendedor.objects.get(pk=request.POST.get("id_vendedor_eliminar"))
            if Venta.objects.filter(id_vendedor=vendedor).exists():
                messages.error(request, "No se puede eliminar: tiene ventas asociadas")
            else:
                vendedor.delete()
                messages.success(request, "Vendedor eliminado")
        except (Vendedor.DoesNotExist, ValueError, TypeError):
            messages.error(request, "Vendedor no encontrado")
    return redirect("Vendedores")


@login_required
def ediciones_view(request):
    return render(
        request,
        "ventas/ediciones.html",
        {
            "Ediciones": EdicionCurso.objects.select_related("id_curso").order_by("-fecha_inicio"),
            "form_edicion": AddEdicionForm(),
            "form_editar_edicion": EditarEdicionForm(),
        },
    )


@login_required
def add_edicion_view(request):
    if request.method == "POST":
        form = AddEdicionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Edición creada")
        else:
            messages.error(request, "Revisa los datos de la edición")
    return redirect("Ediciones")


@login_required
def edit_edicion_view(request):
    if request.method == "POST":
        try:
            edicion = EdicionCurso.objects.get(pk=request.POST.get("id_edicion") or request.POST.get("id_edicion_editar"))
            form = EditarEdicionForm(request.POST, instance=edicion)
            if form.is_valid():
                form.save()
                messages.success(request, "Edición actualizada")
            else:
                messages.error(request, "Revisa los datos de la edición")
        except (EdicionCurso.DoesNotExist, ValueError, TypeError):
            messages.error(request, "Edición no encontrada")
    return redirect("Ediciones")


@login_required
def delete_edicion_view(request):
    if request.method == "POST":
        try:
            edicion = EdicionCurso.objects.get(pk=request.POST.get("id_edicion_eliminar"))
            if VentaDetalle.objects.filter(id_edicion=edicion).exists():
                messages.error(request, "No se puede eliminar: tiene ventas asociadas")
            else:
                edicion.delete()
                messages.success(request, "Edición eliminada")
        except (EdicionCurso.DoesNotExist, ValueError, TypeError):
            messages.error(request, "Edición no encontrada")
    return redirect("Ediciones")


@login_required
def pagos_view(request):
    return render(
        request,
        "ventas/pagos.html",
        {
            "Pagos": Pago.objects.select_related("id_venta", "id_venta__id_cliente").order_by("-fecha_pago"),
            "VentasPendientes": Venta.objects.filter(
                estado="confirmada", estado_pago__in=["pendiente", "parcial"]
            ).select_related("id_cliente"),
            "form_pago": AddPagoForm(),
            "form_editar_pago": EditarPagoForm(),
        },
    )


@login_required
def add_pago_view(request):
    if request.method == "POST":
        form = AddPagoForm(request.POST)
        if form.is_valid():
            pago = form.save()
            pago.id_venta.actualizar_estado_pago()
            messages.success(request, f"Pago #{pago.id_pago} registrado")
        else:
            messages.error(request, "Revisa los datos del pago")
    return redirect("Pagos")


@login_required
def edit_pago_view(request):
    if request.method == "POST":
        try:
            pago = Pago.objects.get(pk=request.POST.get("id_pago") or request.POST.get("id_pago_editar"))
            form = EditarPagoForm(request.POST, instance=pago)
            if form.is_valid():
                pago = form.save()
                pago.id_venta.actualizar_estado_pago()
                messages.success(request, "Pago actualizado")
            else:
                messages.error(request, "Revisa los datos del pago")
        except (Pago.DoesNotExist, ValueError, TypeError):
            messages.error(request, "Pago no encontrado")
    return redirect("Pagos")


@login_required
def delete_pago_view(request):
    if request.method == "POST":
        try:
            pago = Pago.objects.get(pk=request.POST.get("id_pago_eliminar"))
            venta = pago.id_venta
            pago.delete()
            venta.actualizar_estado_pago()
            messages.success(request, "Pago eliminado")
        except (Pago.DoesNotExist, ValueError, TypeError):
            messages.error(request, "Pago no encontrado")
    return redirect("Pagos")
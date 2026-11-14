"""Estado de cuenta de lectura sobre Ventas. No duplica movimientos en SII."""
from decimal import Decimal

from sii.identity import ventas_visibles
from ventas.models import Venta


def estado_cuenta(user):
    ventas = (
        ventas_visibles(user)
        .exclude(estado=Venta.ESTADO_CANCELADA)
        .prefetch_related("pagos", "ventadetalle_set")
        .order_by("-id_venta")
    )
    filas = []
    total_cargos = Decimal("0")
    total_abonos = Decimal("0")
    for venta in ventas:
        cargo = Decimal(venta.monto or 0)
        abonos = sum((pago.monto for pago in venta.pagos.all()), Decimal("0"))
        saldo = cargo - abonos
        total_cargos += cargo
        total_abonos += abonos
        filas.append(
            {
                "venta": venta,
                "cargo": cargo,
                "abonos": abonos,
                "saldo": saldo,
            }
        )
    return {
        "filas": filas,
        "total_cargos": total_cargos,
        "total_abonos": total_abonos,
        "saldo": total_cargos - total_abonos,
        "hay_deuda": (total_cargos - total_abonos) > 0,
    }

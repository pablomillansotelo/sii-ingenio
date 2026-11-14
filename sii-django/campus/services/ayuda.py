from campus.models import TicketAyuda

TRANSICIONES = {
    TicketAyuda.ESTADO_ABIERTO: {
        TicketAyuda.ESTADO_ATENCION,
        TicketAyuda.ESTADO_RESUELTO,
        TicketAyuda.ESTADO_CERRADO,
    },
    TicketAyuda.ESTADO_ATENCION: {
        TicketAyuda.ESTADO_RESUELTO,
        TicketAyuda.ESTADO_CERRADO,
        TicketAyuda.ESTADO_ABIERTO,
    },
    TicketAyuda.ESTADO_RESUELTO: {
        TicketAyuda.ESTADO_CERRADO,
        TicketAyuda.ESTADO_ATENCION,
    },
    TicketAyuda.ESTADO_CERRADO: set(),
}


def puede_transitar(actual, nuevo):
    if actual == nuevo:
        return True
    return nuevo in TRANSICIONES.get(actual, set())

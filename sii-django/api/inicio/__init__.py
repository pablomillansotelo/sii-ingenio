"""Inicio accionable por contexto de trabajo."""

from api.inicio.registro import REGISTRO, registrar, widgets_para  # noqa: F401


def cargar_registro():
    """Importa los módulos de widgets para que llamen a registrar()."""
    from api.inicio import (  # noqa: F401
        widgets_direccion,
        widgets_docente,
        widgets_escolar,
        widgets_ventas,
    )

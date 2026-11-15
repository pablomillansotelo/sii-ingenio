from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Item:
    titulo: str
    meta: str
    url: str
    badge: Optional[str] = None
    badge_tone: Optional[str] = None


@dataclass
class WidgetData:
    count: int
    items: list = field(default_factory=list)
    cta_url: str = ""
    cta_label: str = ""
    ver_todos_url: str = ""
    mensaje_vacio: str = "No hay pendientes."
    severidad: str = "normal"
    tipo: str = "lista"
    kpi: str = ""
    secundario: str = ""
    alerta: str = ""
    alerta_tone: str = ""
    cta_secundario_url: str = ""
    cta_secundario_label: str = ""
    ocultar: bool = False


@dataclass
class Widget:
    clave: str
    titulo: str
    contexto: str
    feature: str
    prioridad: int
    icono: str
    cargar: Callable
    cta_feature: Optional[str] = None
    scope: Optional[str] = None

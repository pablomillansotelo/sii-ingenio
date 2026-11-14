"""Preferencias de apariencia del campus. Una fila por usuario."""

from campus.models import CampusPreferencia


def preferencia_de(user):
    if user is None or not getattr(user, "is_authenticated", False):
        return CampusPreferencia(tema=CampusPreferencia.TEMA_CLARO, acento=CampusPreferencia.ACENTO_ROJO)
    pref, _ = CampusPreferencia.objects.get_or_create(user_id=user.pk)
    return pref

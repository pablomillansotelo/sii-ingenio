def solo_conteo(user):
    return bool(getattr(user, "_inicio_solo_conteo", False))


def memo(request, clave, fn):
    store = getattr(request, "_inicio_memo", None)
    if store is None:
        store = {}
        request._inicio_memo = store
    if clave not in store:
        store[clave] = fn()
    return store[clave]


def memo_user(user, clave, fn):
    store = getattr(user, "_inicio_memo", None)
    if store is None:
        store = {}
        user._inicio_memo = store
    if clave not in store:
        store[clave] = fn()
    return store[clave]

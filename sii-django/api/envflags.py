def as_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text == "":
        return default
    if text in ("1", "true", "t", "yes", "y", "on"):
        return True
    if text in ("0", "false", "f", "no", "n", "off"):
        return False
    return default


def resolver_debug(vercel_env, debug_raw):
    """En Vercel Production el traceback de Django nunca se muestra."""
    if (vercel_env or "") == "production":
        return False
    return as_bool(debug_raw, default=False)

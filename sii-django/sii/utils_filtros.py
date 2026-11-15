def estados_validos(param, choices):
    if not param:
        return []
    permitidos = {valor for valor, _label in choices}
    valores = [parte.strip() for parte in str(param).split(",") if parte.strip()]
    return [valor for valor in valores if valor in permitidos]

class AuthRouter:
    """
    Un router para enviar todos los modelos de autenticación
    a la base de datos 'auth'.
    """
    route_apps = ['auth', 'contenttypes', 'sessions', 'admin']

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_apps:
            return 'auth'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_apps:
            return 'auth'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return True  # normalmente está bien así

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_apps:
            return db == 'auth'
        return db == 'default'
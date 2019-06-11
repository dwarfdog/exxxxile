class MyDBRouter(object):

    def db_for_read(self, model, **hints):
        """
        Attempts to read exile models go to exile_s03.
        """
        if model._meta.app_label == 'exile':
            return 'exile_s03'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write exile models go to exile_s03.
        """
        if model._meta.app_label == 'exile':
            return 'exile_s03'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the exile app is involved.
        """
        if obj1._meta.app_label == 'exile' or \
           obj2._meta.app_label == 'exile':
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the exile app only appears in the 'exile_s03'
        database.
        """
        if app_label == 'exile':
            return db == 'exile_s03'
        return None
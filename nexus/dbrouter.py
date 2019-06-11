class MyDBRouter(object):

    def db_for_read(self, model, **hints):
        """
        Attempts to read nexus models go to exile_nexus.
        """
        if model._meta.app_label == 'nexus':
            return 'exile_nexus'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write nexus models go to exile_nexus.
        """
        if model._meta.app_label == 'nexus':
            return 'exile_nexus'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the nexus app is involved.
        """
        if obj1._meta.app_label == 'nexus' or \
           obj2._meta.app_label == 'nexus':
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the nexus app only appears in the 'exile_nexus'
        database.
        """
        if app_label == 'nexus':
            return db == 'exile_nexus'
        return None
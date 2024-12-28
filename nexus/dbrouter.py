# /nexus/dbrouter.py
"""
Gestionnaire de routage pour les bases de données du projet Django.
Ce fichier définit la logique pour attribuer les lectures/écritures à des bases de données spécifiques basées sur les applications.
"""

class MyDBRouter:
    """
    Routeur pour diriger les requêtes de la base de données à l'instance correcte.
    """

    def db_for_read(self, model, **hints):
        """
        Dirige les lectures des modèles de l'application "nexus" vers la base "exile_nexus".
        """
        if model._meta.app_label == 'nexus':
            return 'exile_nexus'
        return None

    def db_for_write(self, model, **hints):
        """
        Dirige les écritures des modèles de l'application "nexus" vers la base "exile_nexus".
        """
        if model._meta.app_label == 'nexus':
            return 'exile_nexus'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Autorise les relations si au moins un des modèles est associé à l'application "nexus".
        """
        if obj1._meta.app_label == 'nexus' or obj2._meta.app_label == 'nexus':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        S'assure que les migrations pour l'application "nexus" se fassent uniquement sur la base "exile_nexus".
        """
        if app_label == 'nexus':
            return db == 'exile_nexus'
        return None

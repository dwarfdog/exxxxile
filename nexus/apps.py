# /nexus/apps.py

from django.apps import AppConfig

class NexusConfig(AppConfig):
    """
    Configuration de l'application "nexus". Ce fichier permet de personnaliser
    certains comportements globaux de l'application et de définir son nom
    et d'autres métadonnées.
    """
    name = 'nexus'
    verbose_name = "Nexus"

    def ready(self):
        """
        Cette méthode est appelée lorsque l'application est chargée.
        Elle peut être utilisée pour enregistrer des signaux ou effectuer
        d'autres initialisations spécifiques.
        """
        from . import signals  # Import des signaux personnalisés

        # Vous pouvez ajouter ici d'autres initialisations spécifiques si nécessaire
        # Exemple : initialisation des tâches planifiées ou pré-chargement des données

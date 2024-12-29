#!/usr/bin/env python3
# /manage.py
"""
Gestionnaire principal pour les commandes administratives de Django.
Ce fichier configure l'environnement et exécute les commandes Django tout en assurant une meilleure
optimisation et des messages d'erreur explicites.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Chargement des variables d'environnement depuis le fichier .env
load_dotenv()

# Initialisation du logger pour capturer les erreurs
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Point d'entrée principal pour l'exécution des commandes Django.
    """
    try:
        # Configuration de la variable d'environnement pour le module de paramètres Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pyxile.settings')

        # Import de la fonction d'exécution des commandes
        from django.core.management import execute_from_command_line

    except ImportError as exc:
        # Gestion des erreurs d'importation de Django
        logger.error(
            "Impossible d'importer Django. Assurez-vous qu'il est installé et "
            "accessible dans votre PYTHONPATH. Activez l'environnement virtuel si nécessaire."
        )
        raise ImportError(
            "Erreur d'importation de Django. Pour résoudre ce problème, vérifiez :\n"
            "1. Que Django est installé dans l'environnement Python.\n"
            "2. Que la variable PYTHONPATH inclut les chemins appropriés.\n"
            "3. Que votre environnement virtuel est activé."
        ) from exc

    try:
        # Exécution de la commande avec les arguments fournis
        execute_from_command_line(sys.argv)
    except Exception as e:
        # Capture et journalisation des erreurs d'exécution
        logger.critical(f"Une erreur critique est survenue : {e}")
        sys.exit(1)

if __name__ == '__main__':
    """
    Protection contre l'exécution directe si ce fichier est importé comme module.
    """
    main()

# /pyxile/wsgi.py
"""
Configuration WSGI pour le projet Pyxile.

Ce fichier expose l'application WSGI comme une variable de module nommée `application`.
Il assure la configuration initiale de l'environnement et garantit la compatibilité avec les serveurs WSGI.
Pour plus d'informations, voir :
https://docs.djangoproject.com/en/stable/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# Configuration du module de paramètres Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pyxile.settings')

# Instanciation de l'application WSGI
application = get_wsgi_application()
#!/usr/bin/env python3
# /pyxile/urls.py
"""
Fichier de configuration des URLs pour le projet Pyxile.
Ce fichier associe les routes aux vues correspondantes pour l'application Django.
"""

from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from nexus.views import index

# Configuration principale des URLs
urlpatterns = [
    # Page d'accueil
    path('', index, name='home'),

    # Inclusion des URLs des applications principales
    path('exile/', include('exile.urls')),
    path('nexus/', include('nexus.urls')),

    # Accès à l'administration Django
    path('admin/', admin.site.urls),
]

# Ajout de routes pour les fichiers médias en mode DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Inclusion de la toolbar de débogage si activée
    try:
        import debug_toolbar
        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass

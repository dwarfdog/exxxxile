#!/usr/bin/env python3
# /nexus/utils/decorators.py

from functools import wraps
from django.http import HttpResponseRedirect
from django.urls import reverse

def login_required(view_func):
    """
    Décorateur pour vérifier si un utilisateur est connecté.

    Args:
        view_func: La fonction de vue à décorer.

    Returns:
        La fonction décorée ou une redirection vers la page de connexion.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('logged', False):
            return HttpResponseRedirect(reverse('nexus:login'))
        return view_func(request, *args, **kwargs)

    return _wrapped_view

def permission_required(permission):
    """
    Décorateur pour vérifier si un utilisateur possède une permission spécifique.

    Args:
        permission (str): Le nom de la permission à vérifier.

    Returns:
        La fonction décorée ou une redirection vers une page d'erreur.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_permissions = request.session.get('permissions', [])
            if permission not in user_permissions:
                return HttpResponseRedirect(reverse('nexus:permission_denied'))
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator

def admin_required(view_func):
    """
    Décorateur pour restreindre l'accès aux administrateurs uniquement.

    Args:
        view_func: La fonction de vue à décorer.

    Returns:
        La fonction décorée ou une redirection vers une page d'erreur.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('is_admin', False):
            return HttpResponseRedirect(reverse('nexus:permission_denied'))
        return view_func(request, *args, **kwargs)

    return _wrapped_view

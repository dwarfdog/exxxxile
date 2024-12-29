#!/usr/bin/env python3
# /nexus/utils/auth.py

from django.contrib.auth.hashers import check_password
from django.db import connections
from nexus.models import NexusUsers

def authenticate_user(username: str, password: str, request):
    """
    Authentifie un utilisateur en vérifiant son nom d'utilisateur et son mot de passe.

    Args:
        username (str): Le nom d'utilisateur fourni.
        password (str): Le mot de passe fourni.
        request: L'objet de requête pour des métadonnées supplémentaires.

    Returns:
        NexusUsers: L'utilisateur authentifié ou None si les identifiants sont incorrects.
    """
    try:
        # Recherche de l'utilisateur par nom d'utilisateur
        user = NexusUsers.objects.get(username=username)

        # Vérification du mot de passe
        if check_password(password, user.password):
            # Mise à jour de l'empreinte utilisateur si applicable
            fingerprint = request.session.get('fingerprint', None)
            if fingerprint:
                user.fingerprint = fingerprint
                user.save()
            return user

    except NexusUsers.DoesNotExist:
        # Retourne None si l'utilisateur n'existe pas
        return None

    return None



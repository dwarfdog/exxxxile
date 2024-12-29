#!/usr/bin/env python3
# /nexus/utils/auth.py

from django.contrib.auth.hashers import check_password, make_password
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
        with connections['exile_nexus'].cursor() as cursor:
            cursor.execute('SELECT id, username, password FROM nusers WHERE username = %s LIMIT 1', [username])
            user_data = cursor.fetchone()

        if not user_data:
            return None

        user_id, username, hashed_password = user_data

        # Vérification du mot de passe
        if check_password(password, hashed_password):
            # Mise à jour de l'empreinte utilisateur si applicable
            fingerprint = request.session.get('fingerprint', None)
            if fingerprint:
                with connections['exile_nexus'].cursor() as cursor:
                    cursor.execute('UPDATE nusers SET fingerprint = %s WHERE id = %s', [fingerprint, user_id])
            return NexusUsers(id=user_id, username=username, password=hashed_password)

    except Exception as e:
        # Gestion des erreurs, si nécessaire
        return None

    return None

def newpassword(password: str) -> str:
    """
    Génère un nouveau mot de passe haché avec une méthode spécifique.

    Args:
        password (str): Le mot de passe brut.

    Returns:
        str: Un mot de passe haché avec un algorithme prédéfini.
    """
    hashed_password = make_password(password, 'change_password')
    return ''.join([hashed_password[i] for i in range(22, 60, 3)])

def passwordkey(password: str) -> str:
    """
    Génère une clé de validation basée sur le mot de passe.

    Args:
        password (str): Le mot de passe brut.

    Returns:
        str: Une clé unique basée sur le mot de passe.
    """
    hashed_key = make_password(password, 'salt_for_key')
    return ''.join([hashed_key[i] for i in range(22, 60, 3)])

def passwordhash(password: str) -> str:
    """
    Hache un mot de passe avec un algorithme MD5 étendu.

    Args:
        password (str): Le mot de passe brut.

    Returns:
        str: Un hash MD5 sécurisé.
    """
    import hashlib
    return hashlib.md5(('seed' + hashlib.md5(password.encode('utf-8')).hexdigest()).encode('utf-8')).hexdigest()

def is_email_banned(email: str) -> bool:
    """
    Vérifie si un domaine d'e-mail est interdit via une requête SQL.

    Args:
        email (str): L'adresse e-mail à vérifier.

    Returns:
        bool: True si le domaine est interdit, sinon False.
    """
    try:
        with connections['exile_nexus'].cursor() as cursor:
            cursor.execute('SELECT 1 FROM banned_domains WHERE %s ~* domain LIMIT 1', [email])
            return cursor.fetchone() is not None
    except Exception:
        return False

def is_username_banned(username: str) -> bool:
    """
    Vérifie si un nom d'utilisateur est interdit via une requête SQL.

    Args:
        username (str): Le nom d'utilisateur à vérifier.

    Returns:
        bool: True si le nom est interdit, sinon False.
    """
    try:
        with connections['exile_s03'].cursor() as cursor:
            cursor.execute('SELECT 1 FROM banned_logins WHERE %s ~* login LIMIT 1', [username])
            return cursor.fetchone() is not None
    except Exception:
        return False

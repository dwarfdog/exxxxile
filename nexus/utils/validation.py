#!/usr/bin/env python3
# /nexus/utils/validation.py

import re
from django.core.exceptions import ValidationError
from django.core.validators import validate_email as django_validate_email
from django.db import connection

def validate_username(username: str) -> bool:
    """
    Valide le nom d'utilisateur.

    Args:
        username (str): Le nom d'utilisateur à valider.

    Returns:
        bool: True si le nom d'utilisateur est valide, False sinon.
    """
    if len(username) < 2 or len(username) > 12:
        return False
    if not re.match(r'^[a-zA-Z0-9]+$', username):
        return False
    return True

def is_email_banned(email: str) -> bool:
    """
    Vérifie si l'e-mail appartient à un domaine interdit.

    Args:
        email (str): L'adresse e-mail à vérifier.

    Returns:
        bool: True si le domaine est banni, False sinon.
    """
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1 FROM exile_nexus.banned_domains WHERE %s ~* domain LIMIT 1', [email])
        return cursor.fetchone() is not None

def validate_email(email: str) -> bool:
    """
    Valide une adresse e-mail selon les règles de Django.

    Args:
        email (str): L'adresse e-mail à valider.

    Returns:
        bool: True si l'e-mail est valide, False sinon.
    """
    try:
        django_validate_email(email)
        return True
    except ValidationError:
        return False

def is_username_banned(username: str) -> bool:
    """
    Vérifie si un nom d'utilisateur est banni en interrogeant la base de données.

    Args:
        username (str): Le nom d'utilisateur à vérifier.

    Returns:
        bool: True si le nom est banni, False sinon.
    """
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1 FROM exile_s03.banned_logins WHERE %s ~* login LIMIT 1', [username])
        return cursor.fetchone() is not None

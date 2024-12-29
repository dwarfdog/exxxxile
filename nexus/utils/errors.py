#!/usr/bin/env python3
# /nexus/utils/errors.py

error_messages = {
    # Messages d'erreur pour l'inscription
    'username_invalid': "Votre nom d'utilisateur doit être composé de 2 à 12 caractères, uniquement lettres et chiffres.",
    'username_banned': "Ce nom d'utilisateur est réservé, veuillez en choisir un autre.",
    'email_invalid': "L'adresse e-mail saisie est invalide. Veuillez vérifier votre entrée.",
    'email_banned': "Les e-mails provenant de ce domaine ne sont pas autorisés.",
    'accept_conditions': "Vous devez accepter les conditions générales pour vous inscrire.",
    'register_disabled': "Les inscriptions sont temporairement désactivées.",
    'unknown': "Une erreur inconnue s'est produite. Veuillez réessayer plus tard.",

    # Messages d'erreur pour la connexion
    'credentials_invalid': "Nom d'utilisateur ou mot de passe incorrect.",

    # Messages d'erreur pour les permissions
    'permission_denied': "Vous n'avez pas la permission nécessaire pour accéder à cette page.",

    # Messages génériques
    'unexpected_error': "Une erreur inattendue s'est produite. Veuillez réessayer plus tard."
}


def get_error_message(key: str) -> str:
    """
    Récupère un message d'erreur en fonction de la clé fournie.

    Args:
        key (str): La clé du message d'erreur.

    Returns:
        str: Le message d'erreur correspondant ou un message par défaut si la clé est introuvable.
    """
    return error_messages.get(key, error_messages['unexpected_error'])

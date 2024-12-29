#!/usr/bin/env python3
# /nexus/utils/email.py

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def send_registration_email(username: str, email: str, password: str, request) -> bool:
    """
    Envoie un e-mail de confirmation d'inscription à l'utilisateur.

    Args:
        username (str): Le nom d'utilisateur.
        email (str): L'adresse e-mail de l'utilisateur.
        password (str): Le mot de passe généré.
        request: L'objet de requête pour le contexte supplémentaire.

    Returns:
        bool: True si l'e-mail est envoyé avec succès, False sinon.
    """
    try:
        # Générer le contenu de l'e-mail depuis un template
        context = {
            'username': username,
            'password': password,
            'domain': settings.DOMAIN,
        }
        subject = 'Bienvenue sur Exile'
        message = render_to_string('emails/registration_email.txt', context)

        # Envoyer l'e-mail
        send_mail(
            subject,
            message,
            f"contact@{settings.DOMAIN}",
            [email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        # Journaliser l'erreur si nécessaire
        return False

def send_password_reset_email(username: str, email: str, reset_link: str) -> bool:
    """
    Envoie un e-mail de réinitialisation de mot de passe.

    Args:
        username (str): Le nom d'utilisateur.
        email (str): L'adresse e-mail de l'utilisateur.
        reset_link (str): Le lien de réinitialisation de mot de passe.

    Returns:
        bool: True si l'e-mail est envoyé avec succès, False sinon.
    """
    try:
        # Générer le contenu de l'e-mail depuis un template
        context = {
            'username': username,
            'reset_link': reset_link,
            'domain': settings.DOMAIN,
        }
        subject = 'Réinitialisation de votre mot de passe'
        message = render_to_string('emails/password_reset_email.txt', context)

        # Envoyer l'e-mail
        send_mail(
            subject,
            message,
            f"support@{settings.DOMAIN}",
            [email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        # Journaliser l'erreur si nécessaire
        return False

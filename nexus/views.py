#!/usr/bin/env python3
# /nexus/views.py

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpRequest, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import connection, connections
from xml.etree import ElementTree as ET
from django.core.mail import send_mail
from django.contrib import messages
from django.template import loader
from django.conf import settings
from django.urls import reverse
from django.db.models import Q
from xml.dom import minidom
from typing import Optional
from hashlib import md5
import requests
import hashlib
import logging
import secrets
import string
import random
import sys
import re


from nexus.models import *
logger = logging.getLogger('nexus');

################################################ UTILS ################################################
def validate_username(username):
    if not (2 <= len(username) <= 12):
        return False
    return username.isalnum()

def validate_email_address(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False

def is_username_banned(username):
    return BannedLogins.objects.filter(login__iregex=username).exists()

def is_email_banned(email):
    domain = email.split('@')[-1]
    return BannedDomains.objects.filter(domain__iregex=domain).exists()

def generate_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def generate_fingerprint_safe(request, fallback=''):
    try:
        return generate_fingerprint(request)
    except Exception as e:
        logger.warning("Échec de la génération de l'empreinte : %s", str(e))
        return fallback

def fetch_user_from_db(username, password, address, address_forwarded, user_agent):
    try:
        return NexusUsers.objects.raw(
            '''
            SELECT id, username, last_visit, last_universeid, privilege_see_hidden_universes
            FROM sp_account_login(%s, %s, %s, %s, %s)
            LIMIT 1
            ''',
            [username, password, address, address_forwarded, user_agent]
        )[0]
    except (KeyError, IndexError):
        return None

def update_user_session(request, user):
    request.session['user_id'] = user.id
    request.session['logged'] = True
    request.session.modified = True
    logger.debug("Session utilisateur mise à jour : %s", user.id)

def update_fingerprint_in_db(user_id, fingerprint):
    with connections['exile_nexus'].cursor() as cursor:
        cursor.execute(
            'UPDATE nusers SET fingerprint = %s WHERE id = %s',
            [fingerprint, user_id]
        )
    logger.debug("Empreinte mise à jour pour l'utilisateur ID : %s", user_id)

def generate_fingerprint(request) -> str:
    """
    Génère une empreinte unique basée sur l'adresse IP, le User-Agent, et d'autres métadonnées.
    Ajoute un sel statique pour plus de sécurité.

    :param request: L'objet de requête contenant les métadonnées.
    :return: Une empreinte unique sous forme de chaîne hexadécimale.
    """
    # Récupération des données depuis la requête
    address = request.META.get('REMOTE_ADDR', '').strip()
    user_agent = request.headers.get('User-Agent', '').strip()
    forwarded_address = request.META.get('HTTP_X_FORWARDED_FOR', '').strip()

    # Utilisation d'une valeur fallback sécurisée si une donnée est absente
    fallback = "unknown"
    address = address or fallback
    user_agent = user_agent or fallback
    forwarded_address = forwarded_address or fallback

    # Combinaison des données avec un séparateur explicite
    raw_data = f"{address}|{user_agent}|{forwarded_address}"

    # Génération de l'empreinte
    fingerprint = hashlib.sha256(raw_data.encode('utf-8')).hexdigest()

    return fingerprint
################################################ UTILS ################################################


################################################ Page d'erreur 404 ################################################
def page_404(request):
    # Récupérer l'ID utilisateur depuis la session
    user_id = request.session.get('user_id')
    user = None

    # Tenter de récupérer l'utilisateur uniquement si un ID est présent
    if user_id:
        user = NexusUsers.objects.filter(pk=user_id).first()  # Utilise `.filter().first()` pour éviter les exceptions

    # Contexte pour les templates
    context = {
        'content': render(request, 'nexus/404.html', {}).content.decode('utf-8'),
        'logged': request.session.get('logged', False),
        'user': user,
    }

    # Retourner une réponse avec le code HTTP 404
    return HttpResponseNotFound(render(request, 'nexus/master.html', context))


################################################ Page d'accueil ################################################
def index(request):
    """
    Vue pour la page d'accueil.
    Récupère les données utilisateur et les dernières nouvelles pour le contexte.
    """
    t = loader.get_template('nexus/index.html')

    # Gestion de l'utilisateur connecté
    user_id = request.session.get('user_id', 0)
    try:
        logger.debug("Requête : %s", user_id)
        user = NexusUsers.objects.get(pk=user_id)
    except NexusUsers.DoesNotExist:
        user = None

    # Préparation des nouvelles
    news_data = {"news1": [], "news2": []}
    for index, news in enumerate(News.objects.all()):
        try:
            root = ET.fromstring(news.xml)
            for item in root.findall('item'):
                news_item = {
                    "title": item.findtext('title', default=""),
                    "description": item.findtext('description', default="")
                                    .replace('jcolliez', 'Exile')
                                    .replace('http://forum.exil.pw/img/smilies', '/exile/static/exile/assets/smileys'),
                    "author": item.findtext('author', default=""),
                    "pubDate": item.findtext('pubDate', default=""),
                }
                if index == 0:
                    news_data["news1"].append(news_item)
                else:
                    news_data["news2"].append(news_item)
        except ET.ParseError as e:
            logger.error("Erreur d'analyse XML pour la nouvelle %s : %s", news.id, str(e))

    # Construction du contexte
    context = {
        "universes": Universes.objects.all(),
        "content": t.render(news_data, request),
        "logged": request.session.get('logged', False),
        "user": user,
        "lastloginerror": request.session.get('lastloginerror', ""),
    }

    # Rendu final
    return render(request, 'nexus/master.html', context)



################################################ Page de présentation ################################################
def intro(request: HttpRequest) -> HttpResponse:
    # Affiche la page d'introduction du Nexus avec le contexte utilisateur.

    # Récupération de l'utilisateur connecté ou `None` si non trouvé
    user_id = request.session.get('user_id', 0)
    user = NexusUsers.objects.filter(pk=user_id).first()

    # Préparation du contexte
    context = {
        'universes': Universes.objects.all(),  # Charge tous les univers
        'content': render_to_string('nexus/intro.html', {}, request),  # Render du template intro
        'logged': request.session.get('logged', False),  # Statut connecté
        'user': user  # Objet utilisateur
    }

    # Rendu final
    return render(request, 'nexus/master.html', context)



################################################ Page d'enregistrement ################################################
def register(request):
    username = request.POST.get('username', '')
    email = request.POST.get('email', '')
    conditions = request.POST.get('conditions', None)
    error = ''
    content = render_to_string('nexus/register.html', {}, request)
    if request.method == 'POST' and request.POST.get('create', False):
        if settings.MAINTENANCE or settings.REGISTER_DISABLED:
            error = settings.MAINTENANCE and "Les inscriptions sont temporairement désactivées pour maintenance" or "Les inscriptions sont temporairement désactivées"
        else:
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            conditions = request.POST.get('conditions', None)
            error = None

            # Validation des champs
            if not validate_username(username):
                error = "Votre nom d'utilisateur doit être composé de 2 à 12 caractères, lettres et chiffres acceptés."
            elif not validate_email_address(email):
                error = "Veuillez vérifier votre adresse e-mail."
            elif not conditions:
                error = "Vous devez accepter les conditions générales."
            elif is_username_banned(username):
                error = "Ce nom d'utilisateur est réservé."
            elif is_email_banned(email):
                error = "Les emails provenant de ce nom de domaine ne sont pas autorisés."
            else:
                password = generate_password()
                try:
                    with connection.cursor() as cursor:
                        cursor.execute('SET search_path TO exile_nexus,public')
                        cursor.execute('SELECT exile_nexus.sp_account_create(%s, %s, %s, 1036, %s)',
                                        [username, password, email, request.META['REMOTE_ADDR']])
                        result = cursor.fetchone()
                        user_id = result[0] if result else -4
                except Exception:
                    error = "Une erreur est survenue."
                else:
                    if user_id > 0:
                        # Envoi d'email
                        context = {'username': username, 'password': password}
                        message = render_to_string('1036/email_register.txt', context)
                        send_mail(
                            'Exile: registration',
                            message,
                            f'contact@{settings.DOMAIN}',
                            [email],
                            fail_silently=False,
                        )
                        return HttpResponseRedirect(reverse('nexus:registered'))
                    else:
                        error = {
                            -1: "Ce nom d'utilisateur existe déjà.",
                            -2: "Cette adresse e-mail est déjà utilisée.",
                            -3: "Cette adresse IP est déjà utilisée.",
                            -4: "Une erreur est survenue.",
                        }.get(user_id, "Une erreur est survenue.")

    else:
        error = None
        user_id = request.session.get('user_id')

        if user_id:
            try:
                user = NexusUsers.objects.get(pk=user_id)
            except NexusUsers.DoesNotExist:
                pass
            else:
                return HttpResponseRedirect(reverse('nexus:index'))

    context = {
        'logged': request.session.get('logged', False),
        'universes': Universes.objects.all(),
        'content': render_to_string('nexus/register.html', {'username': username, 'email': email, 'conditions': conditions, 'error': error}, request),
        'error': error,
    }
    return render(request, 'nexus/master.html', context)


################################################ Page des questions ################################################
def faq(request):
    user_id = request.session.get('user_id')
    user = None

    if user_id:
        try:
            user = NexusUsers.objects.get(pk=user_id)
        except NexusUsers.DoesNotExist:
            pass

    # Génération du contenu de faq.html comme chaîne de caractères
    faq_content = render_to_string('nexus/faq.html', {}, request)

    # Préparation du contexte principal
    context = {
        'universes': Universes.objects.all(),
        'content': faq_content,  # Injection du contenu rendu
        'logged': request.session.get('logged', False),
        'user': user,
    }

    return render(request, 'nexus/master.html', context)



################################################ Page des bannières ################################################
def banners(request):
    # Initialisation de l'utilisateur
    user = None
    user_id = request.session.get('user_id')

    if user_id:
        try:
            user = NexusUsers.objects.get(pk=user_id)
        except NexusUsers.DoesNotExist:
            logger.warning(f"Utilisateur introuvable pour l'ID {user_id}")
    else:
        logger.info("Aucun ID utilisateur trouvé dans la session.")

    # Préparer le contenu du sous-template
    try:
        banners_content = render_to_string('nexus/banners.html', {}, request)
    except Exception as e:
        logger.error(f"Erreur lors du rendu du sous-template 'nexus/banners.html': {e}")
        banners_content = ""  # Repli en cas d'erreur

    # Préparer le contexte pour le template principal
    context = {
        'universes': Universes.objects.all(),
        'content': banners_content,
        'logged': request.session.get('logged', False),
        'user': user
    }

    # Rendre le template principal
    try:
        return render(request, 'nexus/master.html', context)
    except Exception as e:
        logger.critical(f"Erreur critique lors du rendu du template 'nexus/master.html': {e}")
        # Retour d'une réponse minimale en cas d'erreur critique
        return render(request, 'nexus/error.html', {'message': 'Une erreur critique est survenue.'})


################################################ Page de la liste des serveurs ################################################
################################################     Il faut être connecté     ################################################
def servers(request):
    logger.debug("Session : %s", request.session.items())

    # Vérification de la session
    if not request.session.get('logged', False):
        return HttpResponseRedirect(reverse('nexus:index'))

    # Récupération de l'utilisateur connecté
    user_id = request.session.get('user_id')
    if not user_id:
        return HttpResponseRedirect(reverse('nexus:index'))

    try:
        user = NexusUsers.objects.get(pk=user_id)
        logger.debug("User : %s", user)
    except NexusUsers.DoesNotExist:
        request.session.flush()
        return HttpResponseRedirect(reverse('nexus:index'))

    # Gestion de `getstats`
    getstats = request.GET.get('getstats')
    if getstats:
        try:
            universe = Universes.objects.get(pk=getstats)
        except Universes.DoesNotExist:
            return JsonResponse({'result': ''})

        # Simulation de l'appel à une URL de statistiques
        stats_url = f"{universe.url}/statistics"
        try:
            response = requests.get(stats_url, timeout=3)
            response.raise_for_status()
            return JsonResponse({'result': response.text})
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la récupération des statistiques : {e}")
            return JsonResponse({'result': '{"error":"Problème de communication avec le serveur distant..."}'})

    # Gestion de `setsrv`
    setsrv = request.GET.get('setsrv')
    if setsrv and setsrv.isdigit():
        try:
            user.last_universeid = int(setsrv)
            user.save()
            return HttpResponse(status=204)  # No Content
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'univers : {e}")
            return HttpResponse(status=500)

    # Récupération des univers visibles
    query_filter = "WHERE visible" if not user.privilege_see_hidden_universes else ""
    universes = Universes.objects.raw(
        f"SELECT id, name, description, created, url, login_enabled, players_limit, start_time, stop_time "
        f"FROM universes {query_filter} ORDER BY name"
    )

    # Rendu des templates
    template = loader.get_template('nexus/servers.html')
    context = {
        'universes': universes,
        'content': template.render({'servers': universes}, request),
        'logged': request.session.get('logged', False),
        'user': user,
        'lastloginerror': request.session.get('lastloginerror', '')
    }

    return render(request, 'nexus/master.html', context)



################################################ Page des récompenses ################################################
def account_awards(request):
    user_id = request.session.get('user_id', 0)
    user = NexusUsers.objects.filter(pk=user_id).first()  # Renvoie None si l'utilisateur n'existe pas
    context = {
        'universes': Universes.objects.all(),
        'logged': request.session.get('logged', False),
        'user': user,
    }
    return render(request, 'nexus/master.html', context)


################################################ Page des options utilisateur ################################################
################################################     Il faut être connecté    ################################################
def account_options(request: HttpRequest) -> HttpResponse:
    # Vérification de la session et récupération de l'utilisateur
    user_id = request.session.get('user_id')
    if not user_id:
        # Redirige si l'utilisateur n'est pas connecté
        return redirect('nexus:index') # Redirige vers la page d'accueil

    user = get_object_or_404(NexusUsers, pk=user_id)

    # Préparation du contexte
    context = {
        'universes': Universes.objects.all(),
        'content': render(request, 'nexus/account-options.html', {}).content.decode('utf-8'),
        'logged': request.session.get('logged', False),
        'user': user,
    }

    return render(request, 'nexus/master.html', context)


################################################ Page des conditions d'utilisation ################################################
def conditions(request):
    # Récupérer l'utilisateur connecté
    user = None
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user = NexusUsers.objects.get(pk=user_id)
        except NexusUsers.DoesNotExist:
            user = None

    # Préparer le contexte
    context = {
        'universes': Universes.objects.all(),
        'logged': request.session.get('logged', False),
        'user': user,
    }

    # Rendu du template
    return render(request, 'nexus/master.html', context)



################################################ Page à propos ################################################
def about(request):
    # Récupération de l'utilisateur, avec une valeur par défaut à None
    user_id = request.session.get('user_id')
    user = None
    if user_id:
        user = NexusUsers.objects.filter(pk=user_id).first()  # Évite une exception si l'utilisateur n'existe pas

    # Contexte principal
    context = {
        'universes': Universes.objects.all(),
        'content': render_to_string('nexus/about.html', {}, request),  # Simplifie le rendu du template
        'logged': request.session.get('logged', False),
        'user': user,
    }

    return render(request, 'nexus/master.html', context)


################################################ Fonction de connexion ################################################
def login(request):
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '').strip()

    if not username or not password:
        request.session['lastloginerror'] = 'Champs requis.'
        return HttpResponseRedirect(reverse('nexus:index'))

    logger.debug("Tentative de connexion pour l'utilisateur : %s", username)

    # Récupérer les informations de la requête
    address = request.META.get('REMOTE_ADDR', '')
    address_forwarded = request.get_host()
    user_agent = request.headers.get('User-Agent', '')

    logger.debug("Adresse IP : %s, User-Agent : %s", address, user_agent)

    # Génération de l'empreinte
    fingerprint = generate_fingerprint_safe(request, fallback=address)
    request.session['fingerprint'] = fingerprint
    logger.debug("Empreinte générée : %s", fingerprint)

    # Authentification
    try:
        user = fetch_user_from_db(username, password, address, address_forwarded, user_agent)
        if not user:
            raise ValueError("Utilisateur introuvable ou identifiants invalides.")
    except Exception as e:
        logger.error("Erreur d'authentification : %s", str(e))
        request.session['lastloginerror'] = 'Identifiants invalides.'
        return HttpResponseRedirect(reverse('nexus:index'))

    # Mettre à jour la session utilisateur
    update_user_session(request, user)

    # Mise à jour de l'empreinte dans la base de données
    update_fingerprint_in_db(user.id, fingerprint)

    logger.info("Utilisateur connecté avec succès : %s", username)
    messages.success(request, "Connexion réussie !")
    return HttpResponseRedirect(reverse('nexus:servers'))


################################################ Fonction de déconnexion ################################################
def logout(request):
    try:
        # Récupérer l'utilisateur pour le logging
        user = getattr(request, 'user', AnonymousUser())

        # Logging de l'événement de déconnexion
        if user.is_authenticated:
            logger.info(f"Utilisateur déconnecté : {user.username} (ID: {user.id})")
        else:
            logger.info("Tentative de déconnexion d'un utilisateur anonyme.")

        # Vidage de la session
        request.session.flush()
        messages.success(request, "Déconnexion réussie.")

        # Redirection après déconnexion
        return HttpResponseRedirect(reverse('nexus:index'))

    except Exception as e:
        # Logging de l'erreur
        logger.error(f"Erreur lors de la déconnexion : {e}")
        messages.error(request, "Une erreur est survenue pendant la déconnexion.")

        # Retourner une erreur serveur
        return HttpResponseServerError("Une erreur est survenue pendant la déconnexion.")


################################################ Page de mot de passe perdu ################################################
def lost_password(request):
    def generate_secure_key(password, salt):
        """Generate a secure key using a password and a salt."""
        hashed = make_password(password, salt)
        return ''.join(hashed[i] for i in range(22, 60, 3))

    def generate_password_hash(password):
        """Generate a simple hash of a password (not recommended)."""
        return md5(('seed' + md5(password.encode()).hexdigest()).encode()).hexdigest()

    error = ''
    email = request.POST.get('email', '').strip()
    userid = request.GET.get('id', 0)
    key = request.GET.get('key', '').strip()

    if key and userid:
        try:
            user = NexusUsers.objects.raw(
                'SELECT id, username, password, LCID FROM nusers WHERE id = %s',
                [userid]
            )[0]
        except IndexError:
            error = 'password_not_changed1'
        else:
            if key == generate_secure_key(user.password, 'salt_for_key'):
                try:
                    with connections['exile_nexus'].cursor() as cursor:
                        cursor.execute(
                            'SELECT sp_account_password_set(%s, %s)',
                            [userid, generate_secure_key(user.password, 'change_password')]
                        )
                except Exception as e:
                    error = f'password_not_changed2: {str(e)}'
                else:
                    return HttpResponseRedirect(reverse('nexus:passwordreset'))
            else:
                error = 'password_mismatch'

    if email:
        try:
            validate_email(email)
        except ValidationError:
            error = 'email_invalid'
        else:
            try:
                user = NexusUsers.objects.raw(
                    'SELECT id, username, password FROM nusers WHERE lower(email) = lower(%s)',
                    [email]
                )[0]
            except IndexError:
                error = 'email_not_found'
            else:
                template = loader.get_template(f'1036/email_newpassword.txt') # Utilise le template 1036 pour l'email en français (à adapter)
                context = {
                    'user': user,
                    'password': generate_secure_key(user.password, 'change_password'),
                    'passwordkey': generate_secure_key(user.password, 'salt_for_key')
                }
                try:
                    send_mail(
                        subject='Exile: lostpassword',
                        message=template.render(context, request),
                        from_email=f'contact@{settings.DOMAIN}',
                        recipient_list=[email],
                        fail_silently=False,
                    )
                except Exception as e:
                    error = f'email_send_failure: {str(e)}'
                else:
                    return HttpResponseRedirect(reverse('nexus:passwordsent'))

    universes = Universes.objects.all()
    context = {
        'universes': universes,
        'content': loader.get_template('nexus/lostpassword.html').render({'error': error}, request)
    }
    return render(request, 'nexus/master.html', context)


################################################ Page de mot de passe envoyé ################################################
def password_sent(request):
    # Charger tous les univers
    universes = Universes.objects.all()

    # Générer le contenu du template
    content = render_to_string('nexus/passwordsent.html', request=request)

    # Contexte global
    context = {
        'universes': universes,
        'content': content
    }

    return render(request, 'nexus/master.html', context)


################################################ Page de réinitialisation de mot de passe ################################################
def password_reset(request):
    # Récupération de tous les univers (peu de données, donc acceptable)
    universes = Universes.objects.all()

    # Rendu du contenu partiel directement avec render_to_string
    partial_content = render_to_string('nexus/passwordreset.html', {}, request)

    # Contexte pour le template principal
    context = {
        'universes': universes,
        'content': partial_content
    }

    # Rendu final
    return render(request, 'nexus/master.html', context)


################################################ Page d'inscription réussie ################################################
def registered(request):
    # Récupération optimisée des univers avec une gestion des relations si nécessaire
    universes = Universes.objects.all()

    # Rendu du contenu via le template
    content = render_to_string('nexus/registered.html', {'universes': universes}, request)

    # Contexte général du template parent
    context = {
        'universes': universes,
        'content': content
    }

    return render(request, 'nexus/master.html', context)


################################################ Fonction du changement d'email ################################################
################################################      Il faut être connecté     ################################################
def update_email(request):
    # Vérification de la session et récupération de l'utilisateur
    user_id = request.session.get('user_id')
    if not user_id:
        # Redirige si l'utilisateur n'est pas connecté
        return redirect('nexus:index') # Redirige vers la page d'accueil

    user = get_object_or_404(NexusUsers, pk=user_id)
    error = ""
    if request.method == "POST":
        old_password = request.POST["old_password"]
        email = request.POST["email"]

        if not request.user.check_password(old_password):
            error = "Mot de passe incorrect."
            return HttpResponseRedirect(reverse('nexus:account_options'))

        # Validation et mise à jour de l'email
        try:
            with connections['exile_nexus'].cursor() as cursor:
                cursor.execute(
                    'SELECT sp_account_email_change(%s, %s, %s)',
                    [user.id, old_password, email]
                )
        except Exception as e:
            error = f'email_not_changed: {str(e)}'
        else:
            return HttpResponseRedirect(reverse('nexus:account_options'))

    # Préparation du contexte
    context = {
        'universes': Universes.objects.all(),
        'content': render(request, 'nexus/account-options.html', {}).content.decode('utf-8'),
        'logged': request.session.get('logged', False),
        'user': user,
        'error': error,
    }

    return render(request, 'nexus/master.html', context)

################################################ Fonction du changement de mot de passe ################################################
################################################          Il faut être connecté         ################################################
def update_password(request):
    # Vérification de la session et récupération de l'utilisateur
    user_id = request.session.get('user_id')
    if not user_id:
        # Redirige si l'utilisateur n'est pas connecté
        return redirect('nexus:index') # Redirige vers la page d'accueil

    user = get_object_or_404(NexusUsers, pk=user_id)
    error = ""
    if request.method == "POST":
        old_password = request.POST["old_password"]
        new_password = request.POST["new_password"]
        new_password2 = request.POST["new_password2"]

        if not request.user.check_password(old_password):
            error = "Mot de passe incorrect."
            return HttpResponseRedirect(reverse('nexus:account_options'))

        if new_password != new_password2:
            error = "Les mots de passe ne correspondent pas."
            return HttpResponseRedirect(reverse('nexus:account_options'))

        if len(new_password) < 6 :
            error = "Le mot de passe doit contenir au moins 6 caractères."
            return HttpResponseRedirect(reverse('nexus:account_options'))

        # Mise à jour du mot de passe
        try:
            with connections['exile_nexus'].cursor() as cursor:
                cursor.execute(
                    'SELECT sp_account_password_change(%s, %s, %s)',
                    [user.id, old_password, new_password]
                )
        except Exception as e:
            error = f'password_not_changed: {str(e)}'
        else:
            return HttpResponseRedirect(reverse('nexus:account_options'))

    # Préparation du contexte
    context = {
        'universes': Universes.objects.all(),
        'content': render(request, 'nexus/account-options.html', {}).content.decode('utf-8'),
        'logged': request.session.get('logged', False),
        'user': user,
        'error': error,
    }

    return render(request, 'nexus/master.html', context)
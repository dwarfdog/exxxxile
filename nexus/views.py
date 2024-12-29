#!/usr/bin/env python3
# /nexus/views.py

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.hashers import make_password
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import connection, connections
from django.http import HttpResponseNotFound
from xml.etree import ElementTree as ET
from django.core.mail import send_mail
from django.template import loader
from django.conf import settings
from django.urls import reverse
from django.db.models import Q
from xml.dom import minidom
from typing import Optional
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
################################################ UTILS ################################################


################################################ Page d'erreur 404 ################################################
def page404(request):
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

    context = {
        'universes': Universes.objects.all(),
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

# fonction a faire

def servers(request):
    logger.debug("Session : %s", request.session.items())
    if not request.session.get('logged', False):
        return HttpResponseRedirect(reverse('nexus:index'))
    try:
        user = NexusUsers.objects.get(pk=request.session.get('user_id', 0))
        logger.debug("user : %s", user)
    except (KeyError, NexusUsers.DoesNotExist):
        request.session.flush()
        return HttpResponseRedirect(reverse('nexus:index'))
    getstats = str(request.GET.get('getstats', ''))
    if getstats:
        try:
            universe = Universes.objects.get(pk=getstats)
        except (KeyError, Universes.DoesNotExist):
            return JsonResponse({'result':''})
        # universe.url + '/statistics'
        return JsonResponse({'result':''})
    setsrv = int(request.GET.get('setsrv', 0))
    if setsrv:
        user.last_universeid = setsrv
        user.save()
        return HttpResponse()
    """
    var getstats = Number(Request.QueryString('getstats').item);
    if(!isNaN(getstats)) {
        var rs = SQLConn.execute('SELECT url FROM universes WHERE id=' + getstats);
        
        var url = rs(0).value + '/statistics.asp';
        var xml = Server.CreateObject("MSXML2.ServerXMLHTTP");
        var resultData = '';
        try {
            xml.open("GET", url, true); // True specifies an asynchronous request
            xml.send();
            // Wait for up to 3 seconds if we've not gotten the data yet
            if(xml.readyState != 4)
                xml.waitForResponse(3);
            if(xml.readyState == 4 && xml.status == 200) {
                setExpiration(2);
                resultData = xml.responseText;
            }
            else {
                // Abort the XMLHttp request
                xml.abort();
                throw 0;
            }
        } catch(e) {
            resultData = '{error:"Problem communicating with remote server..."}';
        }
        Response.write(resultData);
        Response.end();
    }
    var setsrv = Number(Request.QueryString('setsrv').item);
    if(!isNaN(setsrv)) {
        SQLConn.execute('SELECT sp_account_universes_set(' + [User.id, setsrv].toSQL() + ')');
        User.setLastUniverseID(setsrv);
        Response.end();
    }
    """
    visible = 'WHERE visible'
    if user.privilege_see_hidden_universes:
        visible = ''
    universes = Universes.objects.raw('SELECT id, name, description, created, url, login_enabled, players_limit, start_time, stop_time FROM universes ' + visible + ' ORDER BY name')
    t = loader.get_template('nexus/servers.html')
    context = {
        'universes': Universes.objects.all(),
        'content': t.render({'servers': universes}, request),
        'logged': request.session.get('logged', False),
        'user': user,
        'lastloginerror': request.session.get('lastloginerror', '')
    }
    return render(request, 'nexus/master.html', context)


################################################ Page des récompenses ################################################
def accountawards(request):
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
# fonction a faire
def conditions(request):
    t = loader.get_template('nexus/conditions.html')
    try:
        user = NexusUsers.objects.get(pk=request.session.get('user_id', 0))
    except (KeyError, NexusUsers.DoesNotExist):
        user = None
    context = {
        'universes': Universes.objects.all(),
        'content': t.render({}, request),
        'logged': request.session.get('logged', False),
        'user': user
    }
    return render(request, 'nexus/master.html', context)


################################################ Page à propos ################################################

def about(request):
    t = loader.get_template('nexus/about.html')
    try:
        user = NexusUsers.objects.get(pk=request.session.get('user_id', 0))
    except (KeyError, NexusUsers.DoesNotExist):
        user = None
    context = {
        'universes': Universes.objects.all(),
        'content': t.render({}, request),
        'logged': request.session.get('logged', False),
        'user': user
    }
    return render(request, 'nexus/master.html', context)


################################################ Fonctions d'empreinte navigateur ################################################

def generate_fingerprint(request):
    """
    Génère une empreinte unique basée sur l'adresse IP, le User-Agent, et d'autres métadonnées.
    """
    address = request.META.get('REMOTE_ADDR', '')
    user_agent = request.headers.get('User-Agent', '')
    forwarded_address = request.META.get('HTTP_X_FORWARDED_FOR', '')

    raw_data = f"{address}|{user_agent}|{forwarded_address}"
    fingerprint = hashlib.sha256(raw_data.encode('utf-8')).hexdigest()

    return fingerprint


################################################ Fonction de connexion ################################################

def login(request):
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '').strip()
    
    logger.debug("username : %s", username)
    logger.debug("password : %s", password)

    if not username or not password:
        # Credentials vides
        request.session['lastloginerror'] = 'credentials_invalid'
        return HttpResponseRedirect(reverse('nexus:index'))

    # Informations utilisateur
    address = request.META.get('REMOTE_ADDR', '')
    addressForwarded = request.get_host()
    userAgent = request.headers.get('User-Agent', '')
    
    logger.debug("address : %s", address)
    logger.debug("addressForwarded : %s", addressForwarded)
    logger.debug("userAgent : %s", userAgent)

    try:
        # Générer une empreinte unique si possible
        try:
            fingerprint = generate_fingerprint(request)
        except Exception:
            fingerprint = address  # Valeur de secours
        request.session['fingerprint'] = fingerprint
        logger.debug("request.session['fingerprint'] : %s", request.session['fingerprint'])

        # Tenter de se connecter en appelant une fonction stockée
        user = NexusUsers.objects.raw(
            '''
            SELECT id, username, last_visit, last_universeid, privilege_see_hidden_universes
            FROM sp_account_login(%s, %s, %s, %s, %s)
            LIMIT 1
            ''',
            [username, password, address, addressForwarded, userAgent]
        )[0]
    except (KeyError, IndexError):
        # Si les identifiants sont incorrects ou l'utilisateur inexistant
        request.session['lastloginerror'] = 'credentials_invalid'
        logger.debug("request.session['lastloginerror'] : %s", request.session['lastloginerror'])
        return HttpResponseRedirect(reverse('nexus:index'))

    # Connexion réussie, mettre à jour les données utilisateur
    request.session['user_id'] = user.id
    request.session['logged'] = True
    request.session.modified = True
    
    logger.debug("request.session['user_id'] : %s", request.session['user_id'])
    logger.debug("request.session['logged'] : %s", request.session['logged'])

    # Mise à jour de l'empreinte dans la base de données
    with connections['exile_nexus'].cursor() as cursor:
        cursor.execute(
            'UPDATE nusers SET fingerprint = %s WHERE id = %s',
            [fingerprint, user.id]
        )

    return HttpResponseRedirect(reverse('nexus:servers'))


################################################ Fonction de déconnexion ################################################

def logout(request):
    request.session.flush()
    return HttpResponseRedirect(reverse('nexus:index'))


################################################ Page de mot de passe perdu ################################################

def lostpassword(request):
    def newpassword(password):
        hash = make_password(password, 'change_password')
        s = ''
        for i in range(22 ,60 ,3):
            s += hash[i]
        return s
    def passwordkey(password):
        hash = make_password(password, 'salt_for_key')
        s = ''
        for i in range(22 ,60 ,3):
            s += hash[i]
        return s
    def passwordhash(password):
        return hashlib.md5('seed'+hashlib.md5(password))
    error = ''
    email = request.POST.get('email', False)
    userid = int(request.GET.get('id', 0))
    key = str(request.GET.get('key', False))
    if key and userid != 0:
        try:
            user = NexusUsers.objects.raw('SELECT id, username, password, LCID FROM nusers WHERE id=%s', [userid])[0]
        except (KeyError, IndexError):
            error = 'password_not_changed1'
        else:
            if(key == passwordkey(user.password)):
                try:
                    with connections['exile_nexus'].cursor() as cursor:
                        cursor.execute('SELECT sp_account_password_set(%s, %s)', [userid, newpassword(user.password)])
                except (KeyError, Exception):
                    error = 'password_not_changed2'
                else:
                    return HttpResponseRedirect(reverse('nexus:passwordreset'))
            else:
                error = 'password_mismatch'
    if email:
        try:
            validate_email(email)
        except (KeyError, ValidationError):
            error = 'email_invalid'
        else:
            try:
                user = NexusUsers.objects.raw('SELECT id, username, password, lcid FROM nusers WHERE lower(email)=lower(%s)', [email])[0]
            except (KeyError, IndexError):
                error = 'email_not_found'
            else:
                t = loader.get_template(str(user.lcid) + '/email_newpassword.txt')
                context = {
                    'user': user,
                    'password': newpassword(user.password),
                    'passwordkey': passwordkey(user.password)
                }
                try:
                    send_mail(
                        'Exile: lostpassword',
                        t.render(context, request),
                        'contact@' + settings.DOMAIN,
                        [email],
                        fail_silently=False,
                    )
                except (KeyError, IndexError):
                    error = 'can\'t send email';
                else:
                    return HttpResponseRedirect(reverse('nexus:passwordsent'))
    t = loader.get_template('nexus/lostpassword.html')
    context = {
        'universes': Universes.objects.all(),
        'content': t.render({'error': error}, request)
    }
    return render(request, 'nexus/master.html', context)


################################################ Page de mot de passe envoyé ################################################

def passwordsent(request):
    t = loader.get_template('nexus/passwordsent.html')
    context = {
        'universes': Universes.objects.all(),
        'content': t.render({}, request)
    }
    return render(request, 'nexus/master.html', context)


################################################ Page de réinitialisation de mot de passe ################################################

def passwordreset(request):
    t = loader.get_template('nexus/passwordreset.html')
    context = {
        'universes': Universes.objects.all(),
        'content': t.render({}, request)
    }
    return render(request, 'nexus/master.html', context)


################################################ Page d'inscription réussie ################################################

def registered(request):
    t = loader.get_template('nexus/registered.html')
    context = {
        'universes': Universes.objects.all(),
        'content': t.render({}, request)
    }
    return render(request, 'nexus/master.html', context)

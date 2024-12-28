# /nexus/views.py

import hashlib
import random
import string
from xml.dom import minidom
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from utils.decorators import login_required
from utils.email import send_registration_email
from utils.errors import error_messages
from utils.fingerprint import generate_fingerprint
from utils.session import get_user_from_session, flush_session
from utils.validation import validate_username, is_email_banned, is_username_banned
from utils.universes import get_visible_universes, set_last_universe
from utils.news import parse_news
from utils.auth import authenticate_user


def page404(request):
    """
    Gère la page 404 avec un contexte utilisateur.
    """
    user = get_user_from_session(request)
    context = {
        'content': render(request, 'nexus/404.html', {}).content,
        'logged': bool(user),
        'user': user
    }
    return render(request, 'nexus/master.html', context)


def index(request):
    """
    Page d'accueil de l'application.
    """
    user = get_user_from_session(request)
    news1 = {}
    news2 = {}
    cpt = 0
    bcpt = 0
    for new in parse_news():
        xmldoc = minidom.parseString(new.xml)
        readbitlist = xmldoc.getElementsByTagName('item')
        for s in readbitlist:
            values = {
                'title': s.getElementsByTagName('title')[0].childNodes[0].data,
                'description': s.getElementsByTagName('description')[0].childNodes[0].data,
                'author': s.getElementsByTagName('author')[0].childNodes[0].data,
                'pubDate': s.getElementsByTagName('pubDate')[0].childNodes[0].data,
            }
            if bcpt == 0:
                news1[cpt] = values.copy()
            else:
                news2[cpt] = values.copy()
            cpt += 1
        bcpt += 1

    context = {
        'universes': get_visible_universes(user),
        'news1': news1,
        'news2': news2,
        'logged': bool(user),
        'user': user,
        'lastloginerror': request.session.get('lastloginerror', '')
    }
    return render(request, 'nexus/master.html', context)


def intro(request):
    """
    Page d'introduction.
    """
    user = get_user_from_session(request)
    context = {
        'universes': get_visible_universes(user),
        'content': render(request, 'nexus/intro.html', {}).content,
        'logged': bool(user),
        'user': user
    }
    return render(request, 'nexus/master.html', context)


def register(request):
    """
    Gère l'inscription utilisateur avec validation.
    """
    if settings.MAINTENANCE or settings.REGISTER_DISABLED:
        error = error_messages['register_disabled']
        return render(request, 'nexus/register.html', {'error': error})

    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    conditions = request.POST.get('conditions')

    error = ''
    if request.method == 'POST':
        if not validate_username(username):
            error = error_messages['username_invalid']
        elif not email or not is_email_banned(email):
            error = error_messages['email_invalid']
        elif not conditions:
            error = error_messages['accept_conditions']
        elif is_username_banned(username):
            error = error_messages['username_banned']
        else:
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            user_created = send_registration_email(username, email, password, request)
            if user_created:
                return HttpResponseRedirect(reverse('nexus:registered'))
            else:
                error = error_messages['unknown']

    user = get_user_from_session(request)
    context = {
        'universes': get_visible_universes(user),
        'error': error,
        'username': username,
        'logged': bool(user),
        'user': user
    }
    return render(request, 'nexus/master.html', context)


@login_required
def servers(request):
    """
    Gère la sélection et l'affichage des serveurs visibles.
    """
    user = get_user_from_session(request)
    getstats = request.GET.get('getstats', '')
    if getstats:
        universe = get_visible_universes(user, pk=getstats)
        return JsonResponse({'result': universe.url + '/statistics'})

    setsrv = request.GET.get('setsrv', 0)
    if setsrv:
        set_last_universe(user, setsrv)
        return HttpResponse()

    universes = get_visible_universes(user)
    context = {
        'universes': universes,
        'logged': True,
        'user': user,
        'content': render(request, 'nexus/servers.html', {'servers': universes}).content,
    }
    return render(request, 'nexus/master.html', context)


def login(request):
    """
    Gère la connexion utilisateur.
    """
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            request.session['lastloginerror'] = 'credentials_invalid'
            return HttpResponseRedirect(reverse('nexus:index'))

        user = authenticate_user(username, password, request)
        if user:
            request.session['user_id'] = user.id
            request.session['logged'] = True
            return HttpResponseRedirect(reverse('nexus:servers'))
        else:
            request.session['lastloginerror'] = 'credentials_invalid'

    return HttpResponseRedirect(reverse('nexus:index'))


def logout(request):
    """
    Gère la déconnexion utilisateur.
    """
    flush_session(request)
    return HttpResponseRedirect(reverse('nexus:index'))

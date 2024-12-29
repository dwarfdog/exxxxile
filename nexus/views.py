#!/usr/bin/env python3
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
from nexus.models import Universes
from nexus.utils.decorators import login_required
from nexus.utils.email import send_registration_email
from nexus.utils.errors import error_messages
from nexus.utils.session import get_user_from_session, flush_session
from nexus.utils.validation import validate_username, is_email_banned, is_username_banned
from nexus.utils.universes import get_visible_universes, set_last_universe
from nexus.utils.news import parse_news
from nexus.utils.auth import authenticate_user, newpassword, passwordkey


def page404(request):
    user = get_user_from_session(request)
    context = {
        'content': render(request, 'nexus/404.html', {}).content,
        'logged': bool(user),
        'user': user
    }
    return render(request, 'nexus/master.html', context)

def index(request):
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
    user = get_user_from_session(request)
    context = {
        'universes': get_visible_universes(user),
        'content': render(request, 'nexus/intro.html', {}).content,
        'logged': bool(user),
        'user': user
    }
    return render(request, 'nexus/master.html', context)

def faq(request):
    user = get_user_from_session(request)
    context = {
        'universes': get_visible_universes(user),
        'content': render(request, 'nexus/faq.html', {}).content,
        'logged': bool(user),
        'user': user
    }
    return render(request, 'nexus/master.html', context)

def conditions(request):
    user = get_user_from_session(request)
    context = {
        'universes': get_visible_universes(user),
        'content': render(request, 'nexus/conditions.html', {}).content,
        'logged': bool(user),
        'user': user
    }
    return render(request, 'nexus/master.html', context)

def about(request):
    user = get_user_from_session(request)
    context = {
        'universes': get_visible_universes(user),
        'content': render(request, 'nexus/about.html', {}).content,
        'logged': bool(user),
        'user': user
    }
    return render(request, 'nexus/master.html', context)

def banners(request):
    user = get_user_from_session(request)
    context = {
        'universes': get_visible_universes(user),
        'content': render(request, 'nexus/banners.html', {}).content,
        'logged': bool(user),
        'user': user
    }
    return render(request, 'nexus/master.html', context)

def registered(request):
    context = {
        'content': render(request, 'nexus/registered.html', {}).content,
    }
    return render(request, 'nexus/master.html', context)

def lostpassword(request):
    user = get_user_from_session(request)
    error = ''
    email = request.POST.get('email', '').strip()
    if email:
        try:
            user = NexusUsers.objects.get(email=email)
            password = newpassword(user.password)
            key = passwordkey(user.password)
            # Logique pour envoyer un e-mail de réinitialisation ici
            return HttpResponseRedirect(reverse('nexus:passwordsent'))
        except NexusUsers.DoesNotExist:
            error = error_messages['email_invalid']

    context = {
        'universes': get_visible_universes(user),
        'content': render(request, 'nexus/lostpassword.html', {'error': error}).content,
        'logged': bool(user),
        'user': user
    }
    return render(request, 'nexus/master.html', context)

def passwordsent(request):
    context = {
        'content': render(request, 'nexus/passwordsent.html', {}).content,
    }
    return render(request, 'nexus/master.html', context)

def passwordreset(request):
    context = {
        'content': render(request, 'nexus/passwordreset.html', {}).content,
    }
    return render(request, 'nexus/master.html', context)

def accountawards(request):
    user = get_user_from_session(request)
    context = {
        'universes': get_visible_universes(user),
        'content': render(request, 'nexus/account-awards.html', {}).content,
        'logged': bool(user),
        'user': user
    }
    return render(request, 'nexus/master.html', context)

def accountoptions(request):
    user = get_user_from_session(request)
    context = {
        'universes': get_visible_universes(user),
        'content': render(request, 'nexus/account-options.html', {}).content,
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
        elif is_email_banned(email):
            error = error_messages['email_banned']
        elif not conditions:
            error = error_messages['accept_conditions']
        elif is_username_banned(username):
            error = error_messages['username_banned']
        else:
            password = newpassword(''.join(random.choices(string.ascii_letters + string.digits, k=8)))
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

def servers(request):
    try:
        user = get_user_from_session(request)
        if not user:
            return HttpResponseRedirect(reverse('nexus:index'))

        getstats = request.GET.get('getstats', '')
        if getstats:
            try:
                universe = Universes.objects.get(pk=getstats)
                return JsonResponse({'result': universe.url + '/statistics'})
            except Universes.DoesNotExist:
                return JsonResponse({'error': 'Universe not found'}, status=404)

        setsrv = request.GET.get('setsrv', 0)
        if setsrv:
            try:
                set_last_universe(user, setsrv)
                return HttpResponse()
            except ValueError as e:
                return JsonResponse({'error': str(e)}, status=400)

        universes = get_visible_universes(user)
        context = {
            'universes': universes,
            'logged': True,
            'user': user,
            'content': render(request, 'nexus/servers.html', {'servers': universes}).content,
        }
        return render(request, 'nexus/master.html', context)

    except Exception as e:
        return JsonResponse({'error': 'An unexpected error occurred', 'details': str(e)}, status=500)

def login(request):
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
    flush_session(request)
    return HttpResponseRedirect(reverse('nexus:index'))

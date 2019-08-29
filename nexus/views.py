import sys, string, random
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.template import loader
from django.core.validators import validate_email
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import connection, connections
import bfa
from xml.dom import minidom

from nexus.models import *

def page404(request):
    t = loader.get_template('nexus/404.html')
    context = {
        'content': t.render({}, request),
        'logged': request.session.get('logged', False),
        'user': user
    }
    return render(request, 'nexus/master.html', context)

# Create your views here.
def index(request):
    t = loader.get_template('nexus/index.html')
    try:
        user = NexusUsers.objects.get(pk=request.session.get('user_id', 0))
    except (KeyError, NexusUsers.DoesNotExist):
        user = None
    context = {
        'news1': {},
        'news2': {}
    }
    cpt=0
    bcpt=0
    for new in News.objects.all():
        xmldoc = minidom.parseString(new.xml)
        readbitlist = xmldoc.getElementsByTagName('item')
        for s in readbitlist:
            print(s.getElementsByTagName('title')[0].childNodes[0].data)
            print(s.getElementsByTagName('description')[0].childNodes[0].data)
            print(s.getElementsByTagName('author')[0].childNodes[0].data)
            print(s.getElementsByTagName('pubDate')[0].childNodes[0].data)
            values = {
                'title': s.getElementsByTagName('title')[0].childNodes[0].data,
                'description': s.getElementsByTagName('description')[0].childNodes[0].data.replace('jcolliez', 'Exile').replace('http://forum.exil.pw/img/smilies','/exile/static/exile/assets/smileys'),
                'author': s.getElementsByTagName('author')[0].childNodes[0].data,
                'pubDate': s.getElementsByTagName('pubDate')[0].childNodes[0].data,
            }
            if bcpt==0:
                context['news1'][cpt] = values.copy()
            else:
                context['news2'][cpt] = values.copy()
            cpt+=1
        bcpt+=1
    context = {
        'universes': Universes.objects.all(),
        'content': t.render(context, request),
        'logged': request.session.get('logged', False),
        'user': user,
        'lastloginerror': request.session.get('lastloginerror', '')
    }
    return render(request, 'nexus/master.html', context)

def intro(request):
    t = loader.get_template('nexus/intro.html')
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

def register(request):
    def isUsernameBanned(username):
        with connection.cursor() as cursor:
            cursor.execute('SET search_path TO exile_nexus,public')
            cursor.execute('SELECT 1 FROM exile_s03.banned_logins WHERE %s ~* login LIMIT 1', [username])
            return cursor.fetchone()
    def isEmailBanned(email):
        with connection.cursor() as cursor:
            cursor.execute('SET search_path TO exile_nexus,public')
            cursor.execute('SELECT 1 FROM exile_nexus.banned_domains WHERE %s ~* domain LIMIT 1', [email])
            return cursor.fetchone()
    def validateUserName(myName):
        if len(myName) < 2 or len(myName) > 12:
            return False
        return myName.isalnum()
    def makePassword(length):
        lettersAndDigits = string.ascii_letters + string.digits
        return ''.join(random.choice(lettersAndDigits) for i in range(length))
    def useridswitch(i):
        switcher = {
            -1: 'Ce nom d\'utilisateur existe déjà, choisissez un nouveau nom',
            -2: 'Cette adresse e-mail est déjà utilisée pour un autre compte, le multi compte est interdit !',
            -3: 'Cette adresse IP est déjà utilisée pour un autre compte, le multi compte est interdit !',
            -4: 'Une erreur est survenue',
        }
        return switcher.get(i,"Une erreur est survenue")

    email_banned = 'Les emails provenant de ce nom de domaine ne sont pas autorisés'
    email_exists = 'Cette adresse e-mail est déjà utilisée pour un autre compte, le multi compte est interdit !'
    email_invalid = 'Veuillez vérifier votre adresse e-mail'
    username_banned = 'Ce nom d\'utilisateur est réservé, choisissez un nouveau nom'
    username_exists = 'Ce nom d\'utilisateur existe déjà, choisissez un nouveau nom'
    username_invalid = 'Votre nom d\'utilisateur doit être composé de 2 à 12 caractères, lettres et chiffres acceptés, vérifiez votre entrée'
    accept_conditions = 'Vous devez accepter les conditions générales pour vous inscrire'
    unknown = 'Une erreur est survenue'
    register_disabled = 'Les inscriptions sont temporairement désactivées'
    register_disabled_maintenance = 'Les inscriptions sont temporairement désactivées pour maintenance'

    username = request.POST.get('username', '')
    email = request.POST.get('email', '')
    conditions = request.POST.get('conditions', None)

    error = ''
    if request.POST.get('create', False):
        if settings.MAINTENANCE or settings.REGISTER_DISABLED:
            if settings.MAINTENANCE:
                error = register_disabled_maintenance
            else:
                error = register_disabled
        if error == '':
            try:
                validate_email(email)
            except (KeyError, ValidationError):
                error = email_invalid
            else:
                if not validateUserName(username):
                    error = username_invalid
                elif conditions is None:
                    error = accept_conditions
                elif isEmailBanned(email):
                    error = email_banned
                elif isUsernameBanned(username):
                    error = username_banned
                else:
                    password = makePassword(8)
                    userid = -4
                    with connection.cursor() as cursor:
                        cursor.execute('SET search_path TO exile_nexus,public')
                        cursor.execute('SELECT exile_nexus.sp_account_create(%s, %s, %s, 1036, %s)', [username, password, email, request.META['REMOTE_ADDR']])
                        res = cursor.fetchone()  
                    try:
                        userid = res[0]
                    except (KeyError, IndexError):
                        error = unknown
                    else:
                        if userid > 0:
                            t = loader.get_template('1036/email_register.txt')
                            context = {
                                'username': username,
                                'password': password
                            }
                            send_mail(
                                'Exile: registration',
                                t.render(context, request),
                                'contact@' + settings.DOMAIN,
                                [email],
                                fail_silently=False,
                            )
                            return HttpResponseRedirect(reverse('nexus:registered'))
                        else:
                            error = useridswitch(userid)
    t = loader.get_template('nexus/register.html')
    try:
        user = NexusUsers.objects.get(pk=request.session.get('user_id', 0))
    except (KeyError, NexusUsers.DoesNotExist):
        user = None
    else:
        return HttpResponseRedirect(reverse('nexus:servers'))
    context = {
        'universes': Universes.objects.all(),
        'content': t.render({'username': username, 'email': email, 'conditions': conditions, 'error': error}, request),
        'logged': request.session.get('logged', False),
        'user': user,
    }
    return render(request, 'nexus/master.html', context)

def faq(request):
    t = loader.get_template('nexus/faq.html')
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

def banners(request):
    t = loader.get_template('nexus/banners.html')
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

def servers(request):
    if not request.session.get('logged', False):
        return HttpResponseRedirect(reverse('nexus:index'))
    try:
        user = NexusUsers.objects.get(pk=request.session.get('user_id', 0))
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

def accountawards(request):
    t = loader.get_template('nexus/account-awards.html')
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

def accountoptions(request):
    t = loader.get_template('nexus/account-options.html')
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

def login(request):
    username = request.POST['username']
    password = password=request.POST['password']
    if username == '' or password == '':
        request.session['lastloginerror'] = 'credentials_invalid'
        return HttpResponseRedirect(reverse('nexus:index'))
    else:
        address = request.META['REMOTE_ADDR']
        addressForwarded = request.get_host()
        userAgent = request.headers.get('User-Agent','')
        try:
            fingerprint = bfa.fingerprint.get(request)
        except (KeyError, Exception):
            fingerprint = address
        #    request.session['lastloginerror'] = 'credentials_invalid'
        #    return HttpResponseRedirect(reverse('nexus:index'))
        request.session['fingerprint'] = fingerprint
        #print(fingerprint)
        # try to log on
        try:
            user = NexusUsers.objects.raw('SELECT id, username, last_visit, last_universeid, privilege_see_hidden_universes FROM sp_account_login(%s, %s, %s, %s, %s) LIMIT 1',[username, password, address, addressForwarded, userAgent])[0]
        except (KeyError, IndexError):
            request.session['lastloginerror'] = 'credentials_invalid'
            return HttpResponseRedirect(reverse('nexus:index'))
        else:
            request.session['user_id'] = user.id
            request.session['logged'] = True
            with connections['exile_nexus'].cursor() as cursor:
                #cursor.execute('SET search_path TO exile_nexus,public')
                cursor.execute('UPDATE nusers SET fingerprint=%s WHERE id=%s', [fingerprint, user.id])
    return HttpResponseRedirect(reverse('nexus:servers'))

def logout(request):
    request.session.flush()
    return HttpResponseRedirect(reverse('nexus:index'))

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
            print(key)
            print(user.password)
            print(passwordkey(user.password))
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
            print(ValidationError)
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

def passwordsent(request):
    t = loader.get_template('nexus/passwordsent.html')
    context = {
        'universes': Universes.objects.all(),
        'content': t.render({}, request)
    }
    return render(request, 'nexus/master.html', context)

def passwordreset(request):
    t = loader.get_template('nexus/passwordreset.html')
    context = {
        'universes': Universes.objects.all(),
        'content': t.render({}, request)
    }
    return render(request, 'nexus/master.html', context)

def registered(request):
    t = loader.get_template('nexus/registered.html')
    context = {
        'universes': Universes.objects.all(),
        'content': t.render({}, request)
    }
    return render(request, 'nexus/master.html', context)

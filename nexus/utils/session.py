#!/usr/bin/env python3
# /nexus/utils/session.py

def get_user_from_session(request):
    """
    Récupère l'utilisateur à partir de la session actuelle.

    Args:
        request: L'objet de requête contenant les informations de session.

    Returns:
        dict: Un dictionnaire contenant les informations utilisateur si connecté, sinon None.
    """
    if not request.session.get('logged', False):
        return None

    user_id = request.session.get('user_id')
    username = request.session.get('username')

    if user_id and username:
        return {
            'id': user_id,
            'username': username,
        }

    return None

def flush_session(request):
    """
    Supprime toutes les données de la session.

    Args:
        request: L'objet de requête contenant la session à effacer.

    Returns:
        None
    """
    request.session.flush()

def update_session_with_user(request, user):
    """
    Met à jour la session avec les informations de l'utilisateur connecté.

    Args:
        request: L'objet de requête contenant la session.
        user: Un objet utilisateur contenant les informations à stocker.

    Returns:
        None
    """
    request.session['logged'] = True
    request.session['user_id'] = user.id
    request.session['username'] = user.username
    request.session['is_admin'] = getattr(user, 'is_admin', False)

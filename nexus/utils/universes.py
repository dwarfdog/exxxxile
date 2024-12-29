#!/usr/bin/env python3
# /nexus/utils/universes.py

from nexus.models import Universes

def get_visible_universes(user=None):
    """
    Récupère les univers visibles pour l'utilisateur donné.

    Args:
        user (dict, optional):  Un dictionnaire contenant les informations utilisateur.
                                Peut inclure des permissions spéciales.

    Returns:
        QuerySet: Une liste des univers visibles.
    """
    if user and user.get('privilege_see_hidden_universes', False):
        return Universes.objects.all().order_by('name')
    return Universes.objects.filter(visible=True).order_by('name')

def set_last_universe(user, universe_id):
    """
    Met à jour le dernier univers sélectionné pour un utilisateur donné.

    Args:
        user (object): L'objet utilisateur à mettre à jour.
        universe_id (int): L'identifiant de l'univers sélectionné.

    Returns:
        None
    """
    if not user:
        raise ValueError("L'utilisateur doit être fourni pour définir un univers.")

    try:
        universe = Universes.objects.get(pk=universe_id)
        user.last_universeid = universe.id
        user.save()
    except Universes.DoesNotExist:
        raise ValueError("L'univers spécifié n'existe pas.")

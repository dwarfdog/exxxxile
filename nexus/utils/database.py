#!/usr/bin/env python3
# /nexus/utils/database.py

from django.db import connections, transaction

def execute_query(query: str, params: list = None, db_alias: str = 'default'):
    """
    Exécute une requête SQL brute sur la base de données spécifiée.

    Args:
        query (str): La requête SQL à exécuter.
        params (list, optional): Les paramètres à injecter dans la requête. Defaults to None.
        db_alias (str, optional): L'alias de la base de données à utiliser. Defaults to 'default'.

    Returns:
        list: Les résultats de la requête sous forme de liste de dictionnaires.
    """
    with connections[db_alias].cursor() as cursor:
        cursor.execute(query, params or [])
        columns = [col[0] for col in cursor.description] if cursor.description else []
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def execute_stored_procedure(proc_name: str, params: list = None, db_alias: str = 'default'):
    """
    Exécute une procédure stockée sur la base de données spécifiée.

    Args:
        proc_name (str): Le nom de la procédure stockée à appeler.
        params (list, optional): Les paramètres à passer à la procédure. Defaults to None.
        db_alias (str, optional): L'alias de la base de données à utiliser. Defaults to 'default'.

    Returns:
        list: Les résultats de la procédure sous forme de liste de dictionnaires.
    """
    query = f"CALL {proc_name}({', '.join(['%s'] * len(params)) if params else ''})"
    return execute_query(query, params, db_alias)

def manage_transaction(queries_with_params: list, db_alias: str = 'default'):
    """
    Gère une transaction impliquant plusieurs requêtes SQL.

    Args:
        queries_with_params (list): Une liste de tuples (requête, paramètres) pour exécuter les requêtes en transaction.
        db_alias (str, optional): L'alias de la base de données à utiliser. Defaults to 'default'.

    Returns:
        bool: True si toutes les requêtes réussissent, False sinon.
    """
    try:
        with transaction.atomic(using=db_alias):
            for query, params in queries_with_params:
                execute_query(query, params, db_alias)
        return True
    except Exception as e:
        # Gérer les erreurs de transaction ici si nécessaire
        return False

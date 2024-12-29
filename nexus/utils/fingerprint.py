#!/usr/bin/env python3
# /nexus/utils/fingerprint.py

import hashlib

def generate_fingerprint(request) -> str:
    """
    Génère une empreinte unique pour un utilisateur basé sur des métadonnées.

    Args:
        request: L'objet de requête HTTP contenant les informations utilisateur.

    Returns:
        str: Une empreinte unique générée.
    """
    address = request.META.get('REMOTE_ADDR', '')
    user_agent = request.headers.get('User-Agent', '')
    forwarded_address = request.META.get('HTTP_X_FORWARDED_FOR', '')

    raw_data = f"{address}|{user_agent}|{forwarded_address}"
    fingerprint = hashlib.sha256(raw_data.encode('utf-8')).hexdigest()

    return fingerprint

def compare_fingerprint(stored_fingerprint: str, request) -> bool:
    """
    Compare une empreinte stockée avec celle générée pour une requête.

    Args:
        stored_fingerprint (str): L'empreinte stockée dans la base de données.
        request: L'objet de requête HTTP contenant les informations utilisateur.

    Returns:
        bool: True si les empreintes correspondent, False sinon.
    """
    current_fingerprint = generate_fingerprint(request)
    return stored_fingerprint == current_fingerprint

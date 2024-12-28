# /nexus/models.py
# Module contenant les modèles Django pour l'application "nexus".

from django.db import models
from exile.models import *


class Awards(models.Model):
    """
    Représente un prix ou une récompense dans le système.
    """
    id = models.AutoField(primary_key=True)
    name = models.TextField(unique=True)

    class Meta:
        managed = True
        db_table = 'exile_nexus.awards'
        verbose_name = "Award"
        verbose_name_plural = "Awards"


class BannedDomains(models.Model):
    """
    Représente un domaine interdit dans le système.
    """
    domain = models.CharField(primary_key=True, max_length=64, unique=True)

    class Meta:
        db_table = 'exile_nexus.banned_domains'
        verbose_name = "Banned Domain"
        verbose_name_plural = "Banned Domains"


class LogLogins(models.Model):
    """
    Journal des tentatives de connexion.
    """
    id = models.BigAutoField(primary_key=True)
    datetime = models.DateTimeField(auto_now_add=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    userid = models.IntegerField(blank=True, null=True)
    address = models.GenericIPAddressField(blank=True, null=True)
    forwarded_address = models.TextField(blank=True, null=True)
    browser = models.CharField(max_length=128, blank=True, null=True)
    success = models.BooleanField()

    class Meta:
        db_table = 'exile_nexus.log_logins'
        verbose_name = "Login Log"
        verbose_name_plural = "Login Logs"


class News(models.Model):
    """
    Actualités ou informations publiées.
    """
    id = models.AutoField(primary_key=True)
    url = models.CharField(unique=True, max_length=200)
    xml = models.TextField()

    class Meta:
        db_table = 'exile_nexus.news'
        verbose_name = "News"
        verbose_name_plural = "News"


class Universes(models.Model):
    """
    Représente un univers de jeu.
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=32)
    visible = models.BooleanField(default=False)
    login_enabled = models.BooleanField(default=True)
    players_limit = models.PositiveIntegerField()
    registration_until = models.DateTimeField(blank=True, null=True)
    ranking_enabled = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    url = models.TextField()
    start_time = models.DateTimeField(blank=True, null=True)
    stop_time = models.DateTimeField(blank=True, null=True)
    has_fastconnect = models.BooleanField(default=False)

    class Meta:
        db_table = 'exile_nexus.universes'
        verbose_name = "Universe"
        verbose_name_plural = "Universes"


class NexusUsers(models.Model):
    """
    Utilisateur du système Nexus.
    """
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=30, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(max_length=255, unique=True)
    lcid = models.PositiveIntegerField()
    registered = models.DateTimeField(auto_now_add=True)
    registration_ip = models.GenericIPAddressField()
    last_visit = models.DateTimeField(auto_now=True)
    last_universeid = models.IntegerField(blank=True, null=True)
    privilege_see_hidden_universes = models.BooleanField(default=False)
    ad_code = models.TextField(blank=True, null=True)
    ad_last_display = models.DateTimeField(blank=True, null=True)
    cheat_detected = models.DateTimeField(blank=True, null=True)
    mail_sent = models.BooleanField()
    fingerprint = models.CharField(max_length=128)

    class Meta:
        db_table = 'exile_nexus.nusers'
        verbose_name = "Nexus User"
        verbose_name_plural = "Nexus Users"


class UsersSuccesses(models.Model):
    """
    Représente les succès déverrouillés par un utilisateur.
    """
    user_id = models.ForeignKey(NexusUsers, on_delete=models.CASCADE, related_name='successes')
    success_id = models.IntegerField()
    universe_id = models.ForeignKey(Universes, on_delete=models.CASCADE, related_name='user_successes')
    added = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'exile_nexus.users_successes'
        verbose_name = "User Success"
        verbose_name_plural = "User Successes"

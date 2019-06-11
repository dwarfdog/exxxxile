# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from exile.models import *


class Awards(models.Model):
    name = models.TextField(unique=True)

    class Meta:
        managed = True
        db_table = 'awards'


class BannedDomains(models.Model):
    domain = models.CharField(primary_key=True, max_length=64, unique=True)

    class Meta:
        managed = True
        db_table = 'exile_nexus.banned_domains'


class LogLogins(models.Model):
    id = models.BigAutoField(primary_key=True)
    datetime = models.DateTimeField()
    username = models.TextField(blank=True, null=True)
    userid = models.IntegerField(blank=True, null=True)
    address = models.GenericIPAddressField(blank=True, null=True)
    forwarded_address = models.TextField(blank=True, null=True)
    browser = models.CharField(max_length=128, blank=True, null=True)
    success = models.BooleanField()

    class Meta:
        managed = True
        db_table = 'exile_nexus.log_logins'


class News(models.Model):
    url = models.CharField(unique=True, max_length=128)
    xml = models.TextField()

    class Meta:
        managed = True
        db_table = 'news'


class Universes(models.Model):
    name = models.CharField(max_length=32)
    visible = models.BooleanField()
    login_enabled = models.BooleanField()
    players_limit = models.IntegerField()
    registration_until = models.DateTimeField(blank=True, null=True)
    ranking_enabled = models.BooleanField()
    created = models.DateTimeField(blank=True, null=True)
    description = models.TextField()
    url = models.TextField()
    start_time = models.DateTimeField(blank=True, null=True)
    stop_time = models.DateTimeField(blank=True, null=True)
    has_fastconnect = models.BooleanField()

    class Meta:
        managed = True
        db_table = 'universes'


class NexusUsers(models.Model):
    username = models.CharField(max_length=16)
    password = models.CharField(max_length=40)
    email = models.CharField(max_length=50)
    lcid = models.IntegerField()
    registered = models.DateTimeField()
    registration_ip = models.GenericIPAddressField()
    last_visit = models.DateTimeField()
    last_universeid = models.IntegerField(blank=True, null=True)
    privilege_see_hidden_universes = models.BooleanField()
    ad_code = models.TextField(blank=True, null=True)
    ad_last_display = models.DateTimeField()
    cheat_detected = models.DateTimeField(blank=True, null=True)
    mail_sent = models.BooleanField()
    fingerprint = models.CharField(max_length=128)

    class Meta:
        managed = True
        db_table = 'nusers'


class UsersSuccesses(models.Model):
    user_id = models.IntegerField()
    success_id = models.IntegerField()
    universe_id = models.IntegerField()
    added = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'users_successes'

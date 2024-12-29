#!/usr/bin/env python3
# /nexus/admin.py

from django.apps import apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from nexus.models import (
    Awards, BannedDomains, LogLogins, News, Universes, NexusUsers, UsersSuccesses
)

# Enregistrement explicite des principaux modèles avec personnalisation
@admin.register(Awards)
class AwardsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')  # Colonnes affichées dans la liste
    search_fields = ('name',)  # Champs inclus dans la barre de recherche
    ordering = ('name',)  # Ordre par défaut

@admin.register(BannedDomains)
class BannedDomainsAdmin(admin.ModelAdmin):
    list_display = ('domain',)  # Affichage du domaine
    search_fields = ('domain',)  # Recherche par domaine
    ordering = ('domain',)  # Tri alphabétique

@admin.register(LogLogins)
class LogLoginsAdmin(admin.ModelAdmin):
    list_display = ('id', 'datetime', 'username', 'success')  # Champs affichés
    list_filter = ('success', 'datetime')  # Filtres par état et date
    search_fields = ('username', 'address')  # Recherche par nom d'utilisateur et IP
    ordering = ('-datetime',)  # Tri par date décroissante

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('id', 'url')
    search_fields = ('url',)  # Recherche par URL
    ordering = ('id',)  # Ordre par ID

@admin.register(Universes)
class UniversesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'visible', 'players_limit', 'created')
    list_filter = ('visible', 'login_enabled', 'ranking_enabled')
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(NexusUsers)
class NexusUsersAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'registered', 'last_visit')
    list_filter = ('privilege_see_hidden_universes', 'registered')
    search_fields = ('username', 'email')
    ordering = ('username',)

@admin.register(UsersSuccesses)
class UsersSuccessesAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'success_id', 'universe_id', 'added')
    list_filter = ('added',)
    ordering = ('-added',)

# Enregistrement dynamique pour tous les modèles non explicitement gérés
app_models = apps.get_app_config('nexus').get_models()
for model in app_models:
    try:
        if not admin.site.is_registered(model):
            admin.site.register(model)
    except AlreadyRegistered:
        pass

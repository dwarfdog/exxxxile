#!/usr/bin/env python3
# /nexus/urls.py
"""
Configuration des URL pour l'application Nexus.
Ce fichier définit les routes disponibles pour l'application Nexus en respectant les pratiques de Django.
"""

from django.urls import path
from . import views

# Nom de l'espace d'application pour éviter les conflits de noms
app_name = 'nexus'

# Liste des routes disponibles
urlpatterns = [
    # Page d'accueil
    path('', views.index, name='index'),

    # Pages générales
    path('intro/', views.intro, name='intro'),
    path('faq/', views.faq, name='faq'),
    path('conditions/', views.conditions, name='conditions'),
    path('about/', views.about, name='about'),

    # Gestion des comptes
    path('register/', views.register, name='register'),
    path('registered/', views.registered, name='registered'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('servers/', views.servers, name='servers'),
    path('lostpassword/', views.lost_password, name='lostpassword'),
    path('passwordsent/', views.password_sent, name='passwordsent'),
    path('passwordreset/', views.password_reset, name='passwordreset'),

    # Options utilisateur
    path('accountawards/', views.account_awards, name='accountawards'),
    path('accountoptions/', views.account_options, name='accountoptions'),

    # Pages spécifiques
    path('banners/', views.banners, name='banners'),
    path('page404/', views.page_404, name='page404'),
    # path('statistics/', views.statistics, name='statistics'), Actuellement non utilisé
]
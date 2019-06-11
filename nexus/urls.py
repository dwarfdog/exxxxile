from django.urls import path#, re_path

from . import views

app_name = 'nexus'
urlpatterns = [
    path('', views.index, name='index'),
    path('intro', views.intro, name='intro'),
    path('register', views.register, name='register'),
    path('registered', views.registered, name='registered'),
    path('faq', views.faq, name='faq'),
    path('banners', views.banners, name='banners'),
    path('servers', views.servers, name='servers'),
    path('accountawards', views.accountawards, name='accountawards'),
    path('accountoptions', views.accountoptions, name='accountoptions'),
    path('logout', views.logout, name='logout'),
    path('conditions', views.conditions, name='conditions'),
    path('about', views.about, name='about'),
    path('login', views.login, name='login'),
    path('lostpassword', views.lostpassword, name='lostpassword'),
    path('passwordsent', views.passwordsent, name='passwordsent'),
    path('passwordreset', views.passwordreset, name='passwordreset'),
    path('statistics', views.passwordreset, name='passwordreset'),
    #re_path(r'^.*$', views.page404, name='page404'),
]
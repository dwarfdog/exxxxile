from django import template
from django.conf import settings
from datetime import datetime

register = template.Library()

# settings value
@register.simple_tag
def settings_value(name):
    return getattr(settings, name, "")

@register.simple_tag
def annee_en_cours():
    return datetime.now().year
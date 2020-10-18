from django import template
from django.contrib.auth.context_processors import PermWrapper
from django.utils import timezone
from sackett import zonehelpers

register = template.Library()


@register.inclusion_tag('sackett/templatetags/nav_menu.html', takes_context=True)
def nav_menu(context):
    request = context['request']
    zones = zonehelpers.get_zones_list()
    return {'perms': PermWrapper(request.user), 'user': request.user, 'zones': zones}

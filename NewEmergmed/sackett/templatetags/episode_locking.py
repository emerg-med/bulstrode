from django import template

register = template.Library()


@register.inclusion_tag('sackett/templatetags/locking_messages.html')
def locking_messages():
    return {}


@register.inclusion_tag('sackett/templatetags/locking_forms.html')
def locking_forms(episode_id):
    return {'episode_id': episode_id}

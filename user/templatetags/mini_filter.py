from django import template

register = template.Library()


@register.filter(name='not_deleted')
def filter_deleted(obj):
    return obj.filter(deleted=False)

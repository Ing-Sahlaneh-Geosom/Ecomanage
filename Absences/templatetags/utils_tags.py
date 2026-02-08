# app/templatetags/utils_tags.py
from django import template

register = template.Library()

@register.filter
def get_item(d, k):
    if not d:
        return None
    return d.get(k)

"""Custom template tags for diary app."""

from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """辞書から指定されたキーの値を取得する

    Usage: {{ dict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def attr(obj, attribute_name):
    """オブジェクトの属性を取得する

    Usage: {{ obj|attr:'attribute_name' }}
    """
    if obj is None:
        return None
    return getattr(obj, attribute_name, None)

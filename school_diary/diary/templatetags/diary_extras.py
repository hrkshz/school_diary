"""Custom template tags for diary app."""

from django import template
from django.contrib.auth import get_user_model

register = template.Library()
User = get_user_model()


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


@register.filter(name="full_name_ja")
def full_name_ja(user):
    """日本語順（姓 名）でフルネームを返す

    Usage: {{ user|full_name_ja }}

    日本では「姓 名」の順序が標準。
    Djangoデフォルトの get_full_name() は英語順（名 姓）なので、
    日本語順に変換するフィルター。
    """
    if user is None:
        return ""
    if isinstance(user, User):
        if user.last_name and user.first_name:
            return f"{user.last_name} {user.first_name}"
        return user.username
    return str(user)

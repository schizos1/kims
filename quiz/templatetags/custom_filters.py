from django import template

register = template.Library()

@register.filter
def get_attr(obj, attr_name):
    """obj에서 attr_name에 해당하는 속성 값을 반환"""
    return getattr(obj, attr_name, '')

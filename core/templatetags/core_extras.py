from django import template

register = template.Library()

@register.filter
def get_option(question, index):
    return getattr(question, f"option{index}")

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

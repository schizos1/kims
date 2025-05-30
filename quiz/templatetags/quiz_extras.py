from django import template

register = template.Library()

@register.filter
def get_choice_text(question, num):
    """
    question 객체에서 'choice{num}_text' 필드를 반환.
    없으면 빈 문자열 반환.
    """
    return getattr(question, f'choice{num}_text', '')

@register.filter
def get_choice_image(question, num):
    """
    question 객체에서 'choice{num}_image' 필드를 반환.
    없으면 빈 문자열 반환.
    """
    return getattr(question, f'choice{num}_image', '')

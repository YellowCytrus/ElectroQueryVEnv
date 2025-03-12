from django import template

register = template.Library()

@register.filter
def filter_session(entries, session):
    return entries.filter(lab_session=session)

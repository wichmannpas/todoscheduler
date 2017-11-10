from datetime import datetime, date
from typing import Union

from django import template


register = template.Library()


@register.filter
def in_past(value: Union[datetime, date]) -> bool:
    if isinstance(value, date):
        return value < date.today()
    return value < datetime.now()


@register.filter
def is_today(value: Union[datetime, date]) -> bool:
    today = date.today()
    if isinstance(value, date):
        return value == today
    return value.date() == today


@register.filter
def multiply(value, arg):
    return value * arg

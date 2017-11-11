from datetime import datetime, date
from typing import Union

from django import template


register = template.Library()


@register.filter
def multiply(value, arg):
    return value * arg


@register.filter
def to_str(value) -> str:
    return str(value)

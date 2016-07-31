# -*- coding: utf-8 -*-

from django import template

register = template.Library()


@register.filter
def percentage(value):
    if value == "-":
        return "-"
    elif value == float("inf"):
        return "+∞%"
    else:
        return "%.2f" % value


@register.filter
def fix_infinity(value):
    """Python’s ∞ prints 'inf', but JavaScript wants 'Infinity'"""
    if value == float("inf"):
        return "Infinity"
    elif value == float("-inf"):
        return "-Infinity"
    else:
        return value

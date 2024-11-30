import os

from django import template

register = template.Library()


@register.simple_tag
def dump_dict(obj):
    return obj.__dict__


@register.filter(name="addcss")
def addcss(field, css):
    return field.as_widget(attrs={"class": css})


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.simple_tag
def attribute_true(request, attribute):
    return True


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

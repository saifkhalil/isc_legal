import os

from django import template
from django.urls import NoReverseMatch, reverse

register = template.Library()

FILE_ICONS = {
    'pdf': 'bi-file-earmark-pdf-fill',
    'doc': 'bi-file-earmark-word-fill',
    'docx': 'bi-file-earmark-word-fill',
    'xls': 'bi-file-earmark-excel-fill',
    'xlsx': 'bi-file-earmark-excel-fill',
    'ppt': 'bi-file-earmark-ppt-fill',
    'pptx': 'bi-file-earmark-ppt-fill',
    'txt': 'bi-file-earmark-text-fill',
    'jpg': 'bi-file-earmark-image-fill',
    'jpeg': 'bi-file-earmark-image-fill',
    'png': 'bi-file-earmark-image-fill',
    'gif': 'bi-file-earmark-image-fill',
    'zip': 'bi-file-earmark-zip-fill',
    'rar': 'bi-file-earmark-zip-fill',
    'mp3': 'bi-file-earmark-music-fill',
    'wav': 'bi-file-earmark-music-fill',
    'mp4': 'bi-file-earmark-play-fill',
    'avi': 'bi-file-earmark-play-fill',
    'mkv': 'bi-file-earmark-play-fill',
}

@register.filter
def file_icon(file_path):
    ext = os.path.splitext(file_path)[1][1:].lower()  # Extract file extension
    return FILE_ICONS.get(ext, 'bi-file-earmark-fill')  # Return default icon if not found


@register.filter
def dict_get(d, key):
    return d.get(key)

@register.filter
def attr(obj, field):
    try:
        return getattr(obj, field)
    except Exception:
        return ""

@register.simple_tag
def url_from_name(name, *args, **kwargs):
    try:
        return reverse(name, args=args, kwargs=kwargs)
    except NoReverseMatch:
        return '#'

@register.filter
def model_name(value):
    return value.__class__.__name__
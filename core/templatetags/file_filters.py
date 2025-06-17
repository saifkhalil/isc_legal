import os

from django import template
from django.urls import NoReverseMatch, reverse
from django.core.cache import cache
from urllib.parse import urlparse, parse_qs, urlencode
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


@register.filter
def is_user_online(user_id):
    return cache.get(f"user_online_{user_id}",False)

@register.filter
def index(indexable, i):
    return indexable[i]

@register.filter
def set_orderby(url: str, field: str):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    current_orderby = query_params.get('orderby', ['modified_by'])
    if current_orderby:
        current_orderby = current_orderby[0]
    if current_orderby == field:
        query_params['orderby'] = [f'-{field}']
    elif current_orderby == f'-{field}':
        query_params['orderby'] = [field]
    else:
        query_params['orderby'] = [field]
    new_query_string = urlencode(query_params, doseq=True)
    new_url = parsed_url._replace(query=new_query_string).geturl()
    return new_url

@register.filter
def same_order(url: str, field: str):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    current_orderby = query_params.get('orderby')
    if current_orderby:
        current_orderby = current_orderby[0]
    reverse_field = f'-{field}'
    if current_orderby == field:
        result = 'same'
    elif current_orderby == reverse_field:
        result = 'reverse'
    else:
        result = 'nothing'

    return result

@register.filter
def preferred_documents(path):
    if hasattr(path, 'filtered_documents') and path.filtered_documents:
        return path.filtered_documents
    return path.documents.all()
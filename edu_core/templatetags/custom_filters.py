# Portfolio\Education_Villa\edu_core\templatetags\custom_filters.py

from django import template
import os

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def basename(value):
    """Extracts the base name of the file path."""
    return os.path.basename(value)

@register.filter
def is_audio_file(file_url):
    """Check if the file URL ends with audio extensions."""
    return file_url.lower().endswith(('.mp3', '.wav', '.m4a'))
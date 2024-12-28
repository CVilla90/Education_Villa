# Education_Villa\edu_core\templatetags\custom_filters.py

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
def convert_file_url(url):
    """Convert file links from Google Drive, Dropbox, etc., into direct links."""
    # Handle Google Drive
    if 'drive.google.com/file/d/' in url:
        file_id = url.split('/file/d/')[1].split('/')[0]
        converted = f'https://drive.google.com/uc?export=view&id={file_id}'
        print(f"Converted Google Drive URL: {converted}")
        return converted
    
    # Handle Dropbox
    if 'dropbox.com' in url:
        if '?dl=0' in url:
            converted = url.replace('?dl=0', '?raw=1')
        elif '?dl=1' not in url and '?raw=1' not in url:
            converted = url + '&raw=1'
        else:
            converted = url
        print(f"Converted Dropbox URL: {converted}")
        return converted
    
    # Default return
    print(f"No conversion applied: {url}")
    return url

@register.filter
def is_audio_file(file_url):
    """Check if the file URL is an audio file."""
    # Explicitly check for supported services
    if 'drive.google.com' in file_url or 'dropbox.com' in file_url:
        print(f"Recognized as audio (Dropbox/Google Drive): {file_url}")
        return True
    if 'soundcloud.com' in file_url:
        print(f"Recognized as audio (SoundCloud): {file_url}")
        return True
    
    # Check for common audio file extensions
    if file_url.lower().endswith(('.mp3', '.wav', '.m4a')):
        print(f"Recognized as audio (File Extension): {file_url}")
        return True

    # Fallback for unrecognized files
    print(f"Not recognized as audio: {file_url}")
    return False

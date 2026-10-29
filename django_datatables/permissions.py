from functools import lru_cache

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string


@lru_cache(maxsize=None)
def permission_check(path):
    try:
        return import_string(path)
    except ImportError as e:
        raise ImproperlyConfigured(f'DJANGO_ADVANCED_PERMISSION_CHECK {path!r} cannot be imported: {e}') from e


def is_permitted(request, kind, name, obj=None):
    path = getattr(settings, 'DJANGO_ADVANCED_PERMISSION_CHECK', None)
    if not path:
        return True
    return bool(permission_check(path)(request, kind, name, obj))

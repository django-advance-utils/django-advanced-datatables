from django.conf import settings
from django.utils.module_loading import import_string


def is_permitted(request, kind, name, obj=None):
    path = getattr(settings, 'DJANGO_ADVANCED_PERMISSION_CHECK', None)
    if not path:
        return True
    return bool(import_string(path)(request, kind, name, obj))

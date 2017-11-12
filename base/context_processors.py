from django.conf import settings


def imprint(request):
    """Return the content of settings.USE_IMPRINT."""
    return {
        'USE_IMPRINT': settings.USE_IMPRINT,
    }

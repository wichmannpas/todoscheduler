from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from django.shortcuts import render


def imprint(request: HttpRequest) -> HttpResponse:
    """Imprint."""
    if not settings.USE_IMPRINT:
        return HttpResponseNotFound()
    return render(request, 'base/imprint.html', {
        'address': settings.IMPRINT_ADDRESS,
    })

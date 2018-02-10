from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserSerializer


class UserView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(
            UserSerializer(request.user).data)


def imprint(request: HttpRequest) -> HttpResponse:
    """Imprint."""
    if not settings.USE_IMPRINT:
        return HttpResponseNotFound()
    return render(request, 'base/imprint.html', {
        'address': settings.IMPRINT_ADDRESS,
    })

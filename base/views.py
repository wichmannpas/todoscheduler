from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserSerializer


class UserView(APIView):
    permission_classes = IsAuthenticated,

    def get(self, request: Request) -> Response:
        return Response(
            UserSerializer(request.user).data)

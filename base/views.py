from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import User
from .serializers import UserSerializer


class UserViewSet(GenericViewSet):
    permission_classes = IsAuthenticated,
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def list(self, request: Request) -> Response:
        instance = request.user
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

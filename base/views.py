from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import RetrieveUpdateAPIView

from .serializers import UserSerializer


class UserView(RetrieveUpdateAPIView):
    permission_classes = IsAuthenticated,
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

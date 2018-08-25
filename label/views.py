from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .serializers import LabelSerializer


class LabelViewSet(ModelViewSet):
    permission_classes = IsAuthenticated,
    serializer_class = LabelSerializer

    def get_queryset(self):
        return self.request.user.labels.all()

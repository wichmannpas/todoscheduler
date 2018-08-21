from django.db.models import F
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import TaskChunkFilterBackend, TaskFilterBackend
from .models import TaskChunk
from .serializers import TaskSerializer, TaskChunkSerializer


class TaskViewSet(viewsets.ModelViewSet):
    filter_backends = TaskFilterBackend,
    permission_classes = (IsAuthenticated,)
    serializer_class = TaskSerializer

    def get_queryset(self):
        queryset = self.request.user.tasks.all()

        return queryset.order_by(F('start').asc(nulls_first=True), 'name')


class TaskChunkViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin,
                       mixins.ListModelMixin, mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin):
    filter_backends = TaskChunkFilterBackend,
    permission_classes = (IsAuthenticated,)
    serializer_class = TaskChunkSerializer

    def get_queryset(self):
        return TaskChunk.objects.filter(task__user=self.request.user)

    def destroy(self, request, pk=None):
        class ParameterSerializer(serializers.Serializer):
            postpone = serializers.BooleanField(default=True)
        params = ParameterSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)

        instance = self.get_object()
        instance.delete(postpone=params.validated_data['postpone'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['POST'], detail=True)
    def split(self, request, pk=None):
        """
        Split a task chunk into two.
        """
        instance = self.get_object()

        class ParameterSerializer(serializers.Serializer):
            duration = serializers.DecimalField(
                max_digits=4, decimal_places=2, default=1)
        params = ParameterSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)

        if instance.finished:
            raise ParseError('finished chunks can not be split')

        duration = params.validated_data['duration']

        if instance.duration <= duration:
            raise ValidationError({
                'duration': 'no duration remains for split'
            })

        serializer = self.get_serializer(
            instance.split(duration), many=True)
        return Response(serializer.data)

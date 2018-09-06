from django.db import transaction
from django.db.models import F
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, ParseError, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import TaskChunkFilterBackend, TaskFilterBackend
from .models import TaskChunk, TaskChunkSeries
from .serializers import TaskSerializer, TaskChunkSerializer, TaskChunkSeriesSerializer


class TaskViewSet(viewsets.ModelViewSet):
    filter_backends = TaskFilterBackend,
    permission_classes = (IsAuthenticated,)
    serializer_class = TaskSerializer

    def get_queryset(self):
        queryset = self.request.user.tasks \
            .prefetch_related('labels') \
            .annotate_scheduled_duration() \
            .annotate_finished_duration()
        return queryset.order_by(F('start').asc(nulls_first=True), 'name')

    @action(['POST'], detail=True, url_path='merge/(?P<other_pk>\d+)')
    def merge(self, request, pk: int, other_pk: int):
        """
        Merge another task into this task.
        """
        instance = self.get_object()
        other_instance = get_object_or_404(self.get_queryset(), pk=other_pk)

        serializer = TaskChunkSerializer(
            instance.merge(other_instance), many=True)
        return Response(serializer.data)


class TaskChunkSeriesViewSet(viewsets.GenericViewSet, mixins.ListModelMixin,
                             mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    permission_classes = IsAuthenticated,
    serializer_class = TaskChunkSeriesSerializer

    def get_queryset(self):
        return TaskChunkSeries.objects.filter(task__user=self.request.user) \
            .select_related('task')

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        scheduled = instance.schedule()
        scheduled_serializer = TaskChunkSerializer(scheduled, many=True)

        return Response({
            'series': serializer.data,
            'scheduled': scheduled_serializer.data,
        }, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed('PATCH')


class TaskChunkViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin,
                       mixins.ListModelMixin, mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin):
    filter_backends = TaskChunkFilterBackend,
    permission_classes = (IsAuthenticated,)
    serializer_class = TaskChunkSerializer

    def get_queryset(self):
        return TaskChunk.objects.filter(task__user=self.request.user) \
            .select_related(
                'task',
                'series',
                'series__task'
            ).prefetch_related('task__chunks', 'task__labels')

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

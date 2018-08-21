from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import TaskExecutionFilterBackend, TaskFilterBackend
from .models import TaskExecution
from .serializers import TaskSerializer, TaskExecutionSerializer


class TaskViewSet(viewsets.ModelViewSet):
    filter_backends = TaskFilterBackend,
    permission_classes = (IsAuthenticated,)
    serializer_class = TaskSerializer

    def get_queryset(self):
        queryset = self.request.user.tasks.all()

        return queryset.order_by(F('start').asc(nulls_first=True), 'name')


class TaskExecutionViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin,
                           mixins.ListModelMixin, mixins.RetrieveModelMixin,
                           mixins.UpdateModelMixin):
    filter_backends = TaskExecutionFilterBackend,
    permission_classes = (IsAuthenticated,)
    serializer_class = TaskExecutionSerializer

    def get_queryset(self):
        return TaskExecution.objects.filter(task__user=self.request.user)

    def destroy(self, request, pk=None):
        class ParameterSerializer(serializers.Serializer):
            postpone = serializers.BooleanField(default=True)
        params = ParameterSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)

        task_execution = get_object_or_404(self.get_queryset(), pk=pk)
        task_execution.delete(postpone=params.validated_data['postpone'])
        return Response(status=status.HTTP_204_NO_CONTENT)

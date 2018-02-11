from datetime import date, timedelta

from django.shortcuts import get_object_or_404
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Task, TaskExecution
from .serializers import DaySerializer, TaskSerializer, TaskExecutionSerializer


class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = TaskSerializer

    def get_queryset(self):
        if 'incomplete' in self.request.query_params:
            return Task.incomplete_tasks(self.request.user)

        return self.request.user.tasks.all()


class TaskExecutionViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin,
                           mixins.CreateModelMixin, mixins.UpdateModelMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = TaskExecutionSerializer

    def get_queryset(self):
        return TaskExecution.objects.filter(task__user=self.request.user)

    def list(self, request):
        def yesterday():
            return date.today() - timedelta(days=1)

        class ParameterSerializer(serializers.Serializer):
            first_day = serializers.DateField(default=yesterday)
            days = serializers.IntegerField(
                default=7,
                min_value=1,
                max_value=100)
        params = ParameterSerializer(data=request.query_params)
        if not params.is_valid():
            return Response(params.errors, status=status.HTTP_400_BAD_REQUEST)

        if 'missed' in request.query_params:
            return Response(self.serializer_class(
                TaskExecution.missed_task_executions(request.user), many=True).data)

        return Response(
            DaySerializer(
                TaskExecution.schedule_by_day(
                    request.user,
                    params.validated_data['first_day'],
                    params.validated_data['days']),
                many=True).data,
        )

    def destroy(self, request, pk=None):
        class ParameterSerializer(serializers.Serializer):
            postpone = serializers.BooleanField(default=True)
        params = ParameterSerializer(data=request.query_params)
        if not params.is_valid():
            return Response(params.errors, status=status.HTTP_400_BAD_REQUEST)

        task_execution = get_object_or_404(self.get_queryset(), pk=pk)
        task_execution.delete(postpone=params.validated_data['postpone'])
        return Response(status=status.HTTP_204_NO_CONTENT)

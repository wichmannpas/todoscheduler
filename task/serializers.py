from rest_framework import serializers

from .models import Task, TaskExecution


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = (
            'name',
            'duration',
        )


class TaskExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskExecution
        fields = (
            'task',
            'day',
            'day_order',
            'duration',
            'finished',
        )
    task = TaskSerializer()


class DaySerializer(serializers.Serializer):
    day = serializers.DateField()
    executions = TaskExecutionSerializer(many=True)

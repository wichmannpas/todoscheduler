from rest_framework import filters, serializers
from rest_framework.exceptions import ValidationError


class TaskExecutionFilterParamsSerializer(serializers.Serializer):
    min_date = serializers.DateField(required=False)
    max_date = serializers.DateField(required=False)
    task_ids = serializers.ListField(
        required=False, child=serializers.IntegerField())

    def validate(self, data):
        validated_data = super().validate(data)

        min_date = validated_data.get('min_date')
        max_date = validated_data.get('max_date')
        if min_date and max_date:
            if max_date < min_date:
                raise ValidationError({
                    'max_date': 'must not be before min_date'
                })

        return validated_data


class TaskExecutionFilterBackend(filters.BaseFilterBackend):
    """
    A filter for task executions.
    It allows to filter by the day of the task execution and by the task.
    """

    def filter_queryset(self, request, queryset, view):
        params = TaskExecutionFilterParamsSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)

        min_date = params.validated_data.get('min_date')
        if min_date:
            queryset = queryset.filter(day__gte=min_date)

        max_date = params.validated_data.get('max_date')
        if max_date:
            queryset = queryset.filter(day__lte=max_date)

        task_ids = params.validated_data.get('task_ids')
        if task_ids:
            queryset = queryset.filter(task_id__in=task_ids)

        return queryset

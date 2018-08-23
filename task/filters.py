from django.db.models import Q
from rest_framework import filters, serializers
from rest_framework.exceptions import ValidationError


class TaskFilterBackend(filters.BaseFilterBackend):
    """
    A filter for tasks.
    """

    def filter_queryset(self, request, queryset, view):
        if 'incomplete' in request.query_params:
            queryset = queryset.incompletely_scheduled()

        return queryset


class TaskChunkFilterParamsSerializer(serializers.Serializer):
    min_date = serializers.DateField(required=False)
    max_date = serializers.DateField(required=False)
    strict_date = serializers.BooleanField(
        default=False,
        help_text='Enforce the date range for unfinished chunks in the past as well')

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


class TaskChunkFilterBackend(filters.BaseFilterBackend):
    """
    A filter for task chunks.
    It allows to filter by the day of the task chunk and by the task.
    """

    def filter_queryset(self, request, queryset, view):
        params = TaskChunkFilterParamsSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)

        min_date = params.validated_data.get('min_date')
        if min_date:
            cond = Q(day__gte=min_date)
            if not params.validated_data['strict_date']:
                cond |= Q(finished=False)

            queryset = queryset.filter(cond)

        max_date = params.validated_data.get('max_date')
        if max_date:
            queryset = queryset.filter(day__lte=max_date)

        task_ids = params.validated_data.get('task_ids')
        if task_ids:
            queryset = queryset.filter(task_id__in=task_ids)

        return queryset

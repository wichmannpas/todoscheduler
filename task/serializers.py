from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Task, TaskExecution


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = (
            'id',
            'name',
            'duration',
            'incomplete_duration',
            'scheduled_duration',
            'finished_duration',
            'default_schedule_duration',
        )
    default_schedule_duration = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True)
    scheduled_duration = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True)
    finished_duration = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True)

    def validate(self, data):
        validated_data = super().validate(data)

        if self.instance and self.instance.pk and 'duration' in validated_data:
            scheduled_duration = self.instance.scheduled_duration
            if validated_data['duration'] < scheduled_duration:
                raise ValidationError({
                    'duration': 'the new duration (%f) is less than the '
                                'scheduled duration (%f).' % (
                                    validated_data['duration'],
                                    scheduled_duration)
                })

        return validated_data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    # TODO: validations for duration update (cf. TaskForm)


class DayOrScheduleField(serializers.DateField):
    """
    A DateField that additionally accepts schedule values.
    """
    def to_representation(self, value):
        return super().to_representation(value)

    def to_internal_value(self, data):
        if data in Task.VALID_SCHEDULE_SPECIAL_DATES:
            # TODO: this low-level access to the request data is not nice.
            task_id = self.context['request'].data.get('task_id')
            if not task_id:
                return super().to_internal_value(data)
            task = self.context['request'].user.tasks.filter(pk=task_id).first()
            if not task:
                return super().to_internal_value(data)
            duration = self.context['request'].data.get('duration')
            if not duration:
                return super().to_internal_value(data)
            try:
                duration = Decimal(duration)
            except ArithmeticError:
                return super().to_internal_value(data)

            day = task.get_day_for_scheduling(
                data, duration)
            if day is None:
                raise ValidationError('no free capacity found in the near future')
            return day

        return super().to_internal_value(data)


class TaskIdRelatedField(serializers.RelatedField):
    def get_queryset(self):
        return self.context['request'].user.tasks.all()

    def to_representation(self, value):
        return value.pk

    def to_internal_value(self, data):
        try:
            self.get_queryset().get(pk=data)
        except ObjectDoesNotExist:
            raise ValidationError('task does not exist')
        return data


class TaskExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskExecution
        fields = (
            'id',
            'task',
            'task_id',
            'day',
            'day_order',
            'duration',
            'finished',
        )
    day = DayOrScheduleField()
    day_order = serializers.IntegerField(max_value=32767, min_value=-32768, required=False)
    task = TaskSerializer(read_only=True)
    task_id = TaskIdRelatedField(write_only=True)

    def create(self, validated_data):
        with transaction.atomic():
            if 'duration' in validated_data:
                task = Task.objects.get(pk=validated_data['task_id'])
                duration_delta = validated_data['duration'] - task.incomplete_duration
                if duration_delta > 0:
                    task.duration += duration_delta
                    task.save()

            return super().create(validated_data)

    def update(self, instance, validated_data):
        with transaction.atomic():
            if 'duration' in validated_data:
                duration_delta = validated_data['duration'] - instance.duration
                if duration_delta:
                    instance.task.duration += duration_delta
                    instance.task.save()

            if 'day_order' in validated_data:
                day = instance.day
                if 'day' in validated_data:
                    day = validated_data['day']
                exchange = TaskExecution.objects.filter(
                    task__user=instance.task.user,
                    day=day,
                    day_order=validated_data['day_order'])
                if len(exchange) == 1:
                    exchange = exchange[0]
                    exchange.day_order = instance.day_order
                    exchange.save(update_fields=('day_order',))

            return super().update(instance, validated_data)


class DaySerializer(serializers.Serializer):
    day = serializers.DateField()
    executions = TaskExecutionSerializer(many=True)
    max_duration = serializers.DecimalField(max_digits=5, decimal_places=2)

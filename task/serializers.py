from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import DefaultDict, List

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import F
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail, ValidationError

from .models import Task, TaskChunk, TaskChunkSeries


class TaskLabelsField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return self.context['request'].user.labels.all()

    def to_internal_value(self, data):
        return super().to_internal_value(data)


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = (
            'id',
            'name',
            'duration',
            'priority',
            'start',
            'deadline',
            'labels',
            'notes',
            'scheduled_duration',
            'finished_duration',
        )
    labels = TaskLabelsField(many=True, required=False)
    scheduled_duration = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True)
    finished_duration = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True)

    def validate(self, data):
        validated_data = super().validate(data)

        errors = {}

        if self.instance and self.instance.pk and 'duration' in validated_data:
            scheduled_duration = self.instance.scheduled_duration
            if validated_data['duration'] < scheduled_duration:
                errors['duration'] = 'the new duration (%f) is less than the ' \
                    'scheduled duration (%f).' % (
                        validated_data['duration'],
                        scheduled_duration)

        start = None
        if self.instance:
            start = self.instance.start
        if 'start' in validated_data:
            start = validated_data['start']

        deadline = None
        if self.instance:
            deadline = self.instance.deadline
        if 'deadline' in validated_data:
            deadline = validated_data['deadline']

        if start and deadline and start > deadline:
            if 'start' in validated_data:
                errors['start'] = 'start date may not be after the deadline'
            if 'deadline' in validated_data:
                errors['deadline'] = 'deadline may not be before the start date'

        if errors:
            raise ValidationError(errors)

        return validated_data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class DayOrScheduleField(serializers.DateField):
    """
    A DateField that additionally accepts schedule values.
    """
    def to_representation(self, value):
        return super().to_representation(value)

    def to_internal_value(self, data):
        if data in Task.VALID_SCHEDULE_SPECIAL_DATES:
            task_id = self.parent.initial_data.get('task_id')
            if not task_id:
                return super().to_internal_value(data)
            try:
                task = self.context['request'].user.tasks.get(pk=task_id)
            except Task.DoesNotExist:
                return super().to_internal_value(data)

            duration = self.parent.initial_data.get('duration')
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

    def to_internal_value(self, data):
        try:
            self.get_queryset().get(pk=data)
        except ObjectDoesNotExist:
            raise ValidationError('task does not exist')
        return data

    def to_representation(self, value):
        return value


class TaskChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskChunk
        fields = (
            'id',
            'task',
            'series',
            'task_id',
            'day',
            'day_order',
            'duration',
            'finished',
            'notes',
        )
    series = serializers.PrimaryKeyRelatedField(read_only=True)
    day = DayOrScheduleField()
    day_order = serializers.IntegerField(max_value=32767, min_value=-32768, required=False)
    task = TaskSerializer(read_only=True)
    task_id = TaskIdRelatedField(write_only=True)

    def create(self, validated_data):
        with transaction.atomic():
            if 'duration' in validated_data:
                task = Task.objects.get(pk=validated_data['task_id'])
                duration_delta = validated_data['duration'] - task.unscheduled_duration
                if duration_delta > 0:
                    task.duration += duration_delta
                    task.save()

            return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        if 'duration' in validated_data:
            duration_delta = validated_data['duration'] - instance.duration
            if duration_delta:
                instance.task.duration += duration_delta
                instance.task.save()

        new_day = validated_data.get('day')
        day_order = validated_data.get('day_order')

        if day_order:
            day = new_day
            if not day:
                day = instance.day

            day_chunks = TaskChunk.objects.filter(
                task__user=self.context['request'].user,
                day=day)
            if day_chunks.filter(day_order=day_order).exists():
                # existing day order was provided, move all other chunks down
                day_chunks.filter(
                    day_order__gte=day_order
                ).update(day_order=F('day_order') + 1)

        if new_day and new_day != instance.day and not day_order:
            # moved to another day without specifying new order, determine it
            day_order = TaskChunk.get_next_day_order(instance.task.user, new_day)

        if day_order:
            validated_data['day_order'] = day_order

        if hasattr(instance.task, '_prefetched_objects_cache'):
            del instance.task._prefetched_objects_cache

        return super().update(instance, validated_data)


class TaskChunkSeriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskChunkSeries
        fields = (
            'id',
            'task_id',
            'duration',
            'start',
            'end',
            'rule',
            'interval_days',
            'monthly_day',
            'monthly_months',
            'monthlyweekday_weekday',
            'monthlyweekday_nth',
        )

    task_id = TaskIdRelatedField()

    def validate_rule(self, value: str) -> str:
        if self.instance and value != self.instance.rule:
            raise ValidationError(
                'changing the rule of an existing series is not allowed')
        return value

    def validate_start(self, value: date) -> str:
        if self.instance and value != self.instance.start:
            raise ValidationError(
                'changing the start of an existing series is not allowed')
        elif not self.instance and value < date.today():
            raise ValidationError(
                'the start date is not allowed to be in the past')
        return value

    def validate_task_id(self, value: int) -> str:
        if self.instance and value != self.instance.task_id:
            raise ValidationError(
                'changing the task of an existing series is not allowed')
        return value

    def validate(self, data):
        rule_fields = {
            'interval_days',
            'monthly_day',
            'monthly_months',
            'monthlyweekday_weekday',
            'monthlyweekday_nth',
        }
        errors = defaultdict(list)
        if data['rule'] == 'interval':
            fields = {
                'interval_days',
            }
            self._update_errors(
                data, errors,
                list(fields),
                list(rule_fields - fields))
        elif data['rule'] == 'monthly':
            fields = {
                'monthly_day',
                'monthly_months',
            }
            self._update_errors(
                data, errors,
                list(fields),
                list(rule_fields - fields))
        elif data['rule'] == 'monthlyweekday':
            fields = {
                'monthly_months',
                'monthlyweekday_weekday',
                'monthlyweekday_nth',
            }
            self._update_errors(
                data, errors,
                list(fields),
                list(rule_fields - fields))

        start = data.get('start')
        monthly_day = data.get('monthly_day')
        if start and monthly_day:
            try:
                data['monthly_day'] = self._validate_monthly_day(start, monthly_day)
            except ValidationError as error:
                errors['monthly_day'].extend(error.detail)

        end = data.get('end')
        if start and end and start > end:
            errors['start'] = 'start date may not be after the end date'
            errors['end'] = 'end date may not be before the start date'

        if errors:
            raise ValidationError(errors)

        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        if validated_data['duration'] != instance.duration:
            # duration changed, update chunks duration
            updated = instance.chunks.filter(duration=instance.duration).update(
                duration=validated_data['duration'])
            additional_duration = updated * (validated_data['duration'] - instance.duration)
            instance.task.duration = F('duration') + additional_duration
            instance.task.save(update_fields=('duration',))
            # refresh the task from the db to get the actual duration value
            instance.task.refresh_from_db()

        return super().update(instance, validated_data)

    def _update_errors(
            self, data: dict, errors: DefaultDict[str, List],
            required: List[str], disallowed: List[str]):
        """
        Update the errors dict in-place to reflect violations of
        the required and disallowed fields.
        """
        for field in required:
            if data.get(field) is None:
                if field not in errors:
                    errors[field] = []
                errors[field].append(ErrorDetail('This field is required.', code='required'))
        for field in disallowed:
            if data.get(field) is not None:
                if field not in errors:
                    errors[field] = []
                errors[field].append(ErrorDetail('This field is not allowed.', code='disallowed'))

    def _validate_monthly_day(self, start: date, monthly_day: int) -> int:
        """
        Validate the monthly day based on the start date.
        """
        last_day_of_month = False
        if (start + timedelta(days=1)).month != start.month:
            last_day_of_month = True

        if not last_day_of_month and start.day != monthly_day:
            raise ValidationError('monthly day must be the same as the day of the start date')

        return monthly_day

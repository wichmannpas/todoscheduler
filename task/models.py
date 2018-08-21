from typing import Union

from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Sum, F, Max, QuerySet
from django.db.models.functions import Coalesce


class TaskQuerySet(models.QuerySet):
    def filter_incomplete(self):
        return self.annotate(
            scheduled_duration_agg=Coalesce(
                Sum('executions__duration'),
                0)).annotate(
            incomplete_duration_agg=F(
                'duration') - F('scheduled_duration_agg')
        ).filter(incomplete_duration_agg__gt=0)


class TaskManager(models.Manager):
    def get_queryset(self):
        return TaskQuerySet(self.model, using=self._db)

    def filter_incomplete(self):
        return self.get_queryset().filter_incomplete()


class Task(models.Model):
    """A task is a single job to do."""

    VALID_SCHEDULE_SPECIAL_DATES = (
        'today',
        'tomorrow',
        'next_free_capacity',
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks')
    name = models.CharField(max_length=40)
    duration = models.DecimalField(
        max_digits=5, decimal_places=2, default=1,
        validators=(
            MinValueValidator(Decimal('0.01')),
        ))

    start = models.DateField(null=True)

    objects = TaskManager()

    def __str__(self) -> str:
        return '{}: {}'.format(self.user, self.name)

    @property
    def finished_duration(self) -> Decimal:
        if hasattr(self, 'finished_duration_agg'):
            return self.finished_duration_agg
        return self.executions.filter(finished=True).aggregate(
            Sum('duration'))['duration__sum'] or Decimal(0)

    @property
    def scheduled_duration(self) -> Decimal:
        if hasattr(self, 'scheduled_duration_agg'):
            return self.scheduled_duration_agg
        return self.executions.aggregate(Sum('duration'))['duration__sum'] or Decimal(0)

    @property
    def incomplete_duration(self) -> Decimal:
        """Get the duration of this task which is not yet scheduled."""
        if hasattr(self, 'incomplete_duration_agg'):
            return self.incomplete_duration_agg
        return (
            self.duration -
            (self.executions.aggregate(Sum('duration'))['duration__sum'] or Decimal(0)))

    @property
    def default_schedule_duration(self) -> Decimal:
        """
        Get the duration that should be suggested for scheduling
        based on the user preferences.
        """
        incomplete_duration = self.incomplete_duration
        if (
                incomplete_duration <= self.user.default_schedule_full_duration_max or
                incomplete_duration <= self.user.default_schedule_duration):
            return incomplete_duration
        return self.user.default_schedule_duration

    def get_day_for_scheduling(
            self, special_date: str, duration: Decimal) -> Union[None, date]:
        """
        Get the day for a task execution by a special day string (i.e., 'today').
        """
        if special_date == 'today':
            return date.today()
        elif special_date == 'tomorrow':
            return date.today() + timedelta(days=1)
        elif special_date == 'next_free_capacity':
            if (duration > self.user.workhours_weekday and
                    duration > self.user.workhours_weekend):
                # does not fit in a single day
                return None
            today = date.today()
            # TODO: aggregate this in the database!
            for offset in range(90):
                cur_day = today + timedelta(days=offset)
                if Task.free_capacity(self.user, cur_day) >= duration:
                    return cur_day
            return None

        raise ValueError('unknown special_date value: %s' % special_date)

    @staticmethod
    def free_capacity(user: get_user_model(), day: date) -> Decimal:
        """Get the free capacity of a day."""
        used_capacity = TaskExecution.objects.filter(
            task__user=user, day=day).aggregate(
            used_capacity=Sum('duration')
        )['used_capacity'] or 0
        total_capacity = user.capacity_of_day(day)
        return total_capacity - used_capacity


class TaskExecution(models.Model):
    """An execution of a task."""

    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name='executions')
    day = models.DateField()
    day_order = models.SmallIntegerField()
    duration = models.DecimalField(
        max_digits=4, decimal_places=2, default=1,
        validators=(
            MinValueValidator(Decimal('0.01')),
        ))
    finished = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.day_order is None and not self.pk and self.day and self.task:
            self.day_order = TaskExecution.get_next_day_order(
                self.task.user, self.day)

    def __str__(self) -> str:
        return '{}: {}'.format(self.task, self.day)

    def delete(self, postpone: bool = True):
        """
        Delete this task execution.

        When not postponed, the duration of the task is reduced by the
        duration of this task execution.
        """
        with transaction.atomic():
            if not postpone:
                task = self.task
                task.duration -= self.duration
                if task.duration <= 0:
                    task.delete()
                else:
                    task.save(update_fields=('duration',))
            super().delete()

    @staticmethod
    def get_next_day_order(user, day):
        """Get the next day order for a specific day."""
        return (TaskExecution.objects.filter(
            task__user=user,
            day=day).aggregate(Max('day_order'))['day_order__max'] or 0) + 1

    @staticmethod
    def missed_task_executions(user: get_user_model()) -> QuerySet:
        """Get all unfinished task executions scheduled for a past day."""
        return TaskExecution.objects.filter(
            task__user=user,
            day__lt=date.today(),
            finished=False
        ).order_by('day').select_related('task')

from typing import List, Union

from datetime import date, timedelta

from collections import OrderedDict
from decimal import Decimal
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Sum, F, Max
from django.db.models.functions import Coalesce

from .day import Day


class Task(models.Model):
    """A task is a single job to do."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks')
    name = models.CharField(max_length=40)
    duration = models.DecimalField(
        max_digits=5, decimal_places=2, default=1)

    def __str__(self) -> str:
        return '{}: {}'.format(self.user, self.name)

    def schedule(self,
                 schedule_for: str, schedule_for_date: date,
                 duration: Decimal) -> Union[None, date]:
        """
        Schedule execution of this task.
        Returns whether the chosen day had enough capacities.
        """
        if schedule_for == 'today':
            day = date.today()
        elif schedule_for == 'tomorrow':
            day = date.today() + timedelta(days=1)
        elif schedule_for == 'next_free_capacity':
            if (duration > self.user.workhours_weekday and
                    duration > self.user.workhours_weekend):
                # does not fit in a single day
                return None
            day = None
            today = date.today()
            # TODO: aggregate this in the database!
            for offset in range(90):
                cur_day = today + timedelta(days=offset)
                if Task.free_capacity(self.user, cur_day) >= duration:
                    day = cur_day
                    break
            if day is None:
                return None
        elif schedule_for == 'another_time':
            day = schedule_for_date
        else:
            raise ValueError('unknown schedule_for value: %s' % schedule_for)

        day_order = (TaskExecution.objects.filter(
            task__user=self.user,
            day=day).aggregate(Max('day_order'))['day_order__max'] or 0) + 1
        TaskExecution.objects.create(
            task=self,
            day=day,
            day_order=day_order,
            duration=duration)
        # TODO: check day capacity
        return day

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
    def unscheduled_duration(self) -> Decimal:
        """Get the duration of this task which is not yet scheduled."""
        if hasattr(self, 'unscheduled_duration_agg'):
            return self.unscheduled_duration_agg
        return (
            self.duration -
            (self.executions.aggregate(Sum('duration'))['duration__sum'] or Decimal(0)))

    @property
    def default_schedule_duration(self) -> Decimal:
        """
        Get the duration that should be suggested for scheduling
        based on the user preferences.
        """
        unscheduled_duration = self.unscheduled_duration
        if (
                unscheduled_duration <= self.user.default_schedule_full_duration_max or
                unscheduled_duration <= self.user.default_schedule_duration):
            return unscheduled_duration
        return self.user.default_schedule_duration

    @staticmethod
    def unscheduled_tasks(user: get_user_model()):
        """Get all tasks which are not yet fully scheduled."""
        return user.tasks.annotate(
            scheduled_duration_agg=Coalesce(
                Sum('executions__duration'),
                0)).annotate(
            unscheduled_duration_agg=F(
                'duration') - F('scheduled_duration_agg')
        ).filter(unscheduled_duration_agg__gt=0)

    @staticmethod
    def free_capacity(user: get_user_model(), day: date) -> Decimal:
        """Get the free capacity of a day."""
        executions = TaskExecution.objects.filter(
            task__user=user, day=day)
        day = Day(user, day)
        day.executions = list(executions)
        return day.available_duration


class TaskExecution(models.Model):
    """An execution of a task."""
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name='executions')
    day = models.DateField()
    day_order = models.SmallIntegerField()
    duration = models.DecimalField(
        max_digits=4, decimal_places=2, default=1)
    finished = models.BooleanField(default=False)

    def __str__(self) -> str:
        return '{}: {}'.format(self.task, self.day)

    def overdue(self) -> bool:
        """Check wheter the execution is overdue."""
        return self.past and not self.finished

    @property
    def past(self) -> bool:
        """Check wheter the execution lies in the past."""
        return self.day < date.today()

    @staticmethod
    def schedule_by_day(
            user: get_user_model(),
            first_day: date, days: int) -> List[Day]:
        """Get an overview of the schedule."""
        last_day = first_day + timedelta(days)
        executions = TaskExecution.objects.filter(task__user=user).filter(
                day__gte=first_day, day__lte=last_day).select_related('task').order_by(
                    'day', '-finished', 'day_order')

        by_day = OrderedDict()
        day = first_day
        # ensure that all days (even those without execution) are in the dictionary
        while day <= last_day:
            by_day[day] = Day(user, day)
            day += timedelta(days=1)
        for execution in executions:
            by_day[execution.day].executions.append(execution)
        return by_day.values()

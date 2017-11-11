from typing import List, Dict

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
    estimated_duration = models.DecimalField(
        max_digits=5, decimal_places=2, default=1)

    def __str__(self) -> str:
        return '{}: {}'.format(self.user, self.name)

    def schedule(self,
                 schedule_for: str, schedule_for_date: date,
                 duration: Decimal) -> bool:
        """
        Schedule execution of this task.
        Returns whether the chosen day had enough capacities.
        """
        if schedule_for == 'today':
            day = date.today()
        elif schedule_for == 'tomorrow':
            day = date.today() + timedelta(days=1)
        elif schedule_for == 'next_free_capacity':
            raise NotImplementedError
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
        return True

    @property
    def unscheduled_duration(self):
        """Get the duration of this task which is not yet scheduled."""
        if hasattr(self, 'unscheduled_duration_agg'):
            return self.unscheduled_duration_agg
        return (
            self.estimated_duration -
            (self.executions.aggregate(Sum('duration'))['duration__sum'] or 0))

    @staticmethod
    def unscheduled_tasks(user: get_user_model()):
        """Get all tasks which are not yet fully scheduled."""
        return user.tasks.annotate(
            scheduled_duration=Coalesce(
                Sum('executions__duration'),
                0),
            unscheduled_duration_agg=F(
                'estimated_duration') - F('scheduled_duration')
        ).filter(unscheduled_duration_agg__gt=0)


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

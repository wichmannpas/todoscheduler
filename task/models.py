from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Sum, F
from django.db.models.functions import Coalesce


class Task(models.Model):
    """A task is a single job to do."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks')
    name = models.CharField(max_length=40)
    estimated_duration = models.DecimalField(
        max_digits=3, decimal_places=2, default=1)

    def __str__(self) -> str:
        return '{}: {}'.format(self.user, self.name)

    @property
    def unscheduled_duration(self):
        """Get the duration of this task which is not yet scheduled."""
        if hasattr(self, 'unscheduled_duration_agg'):
            return self.unscheduled_duration_agg
        return (
            self.estimated_duration -
            self.executions.aggregate(Sum('duration'))['duration__sum'] or 0)

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
    duration = models.DecimalField(
        max_digits=3, decimal_places=2, default=1)
    finished = models.BooleanField(default=False)

    def __str__(self) -> str:
        return '{}: {}'.format(self.task, self.day)

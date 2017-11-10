from django.conf import settings
from django.db import models


class Task(models.Model):
    """A task is a single job to do."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks')
    name = models.CharField(max_length=40)
    estimated_duration = models.DecimalField(
        max_digits=3, decimal_places=2, default=1)

    def __str__(self) -> str:
        return '{}: {}'.format(self.user, self.name)


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

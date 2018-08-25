from django.conf import settings
from django.db import models


class Label(models.Model):
    class Meta:
        unique_together = (
            'user',
            'title',
        )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='labels')

    title = models.CharField(max_length=15)
    description = models.TextField()
    color = models.CharField(max_length=6)

    def __str__(self) -> str:
        return '{}: {}'.format(
            str(self.user),
            self.title)

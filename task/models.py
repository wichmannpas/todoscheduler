from typing import List, Union

from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Sum, F, Max, Q, QuerySet
from django.db.models.functions import Coalesce


class TaskQuerySet(models.QuerySet):
    def annotate_finished_duration(self):
        return self.annotate(
            finished_duration_agg=Coalesce(
                Sum('chunks__duration', filter=Q(chunks__finished=True)),
                0))

    def annotate_scheduled_duration(self):
        return self.annotate(
            scheduled_duration_agg=Coalesce(
                Sum('chunks__duration'),
                0))

    def incompletely_scheduled(self):
        """
        Filter this QuerySet for tasks that have not been completely
        scheduled yet.
        """
        return self.annotate_scheduled_duration().annotate(
            unscheduled_duration_agg=F(
                'duration') - F('scheduled_duration_agg')
        ).filter(unscheduled_duration_agg__gt=0)


class TaskManager(models.Manager):
    def get_queryset(self):
        return TaskQuerySet(self.model, using=self._db)

    def annotate_finished_duration(self):
        return self.get_queryset().annotate_finished_duration()

    def annotate_scheduled_duration(self):
        return self.get_queryset().annotate_scheduled_duration()

    def incompletely_scheduled(self):
        return self.get_queryset().incompletely_scheduled()


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
    def completely_scheduled(self) -> bool:
        return self.scheduled_duration == self.duration

    @property
    def finished(self) -> bool:
        return self.finished_duration == self.duration

    @property
    def scheduled_duration(self) -> Decimal:
        if hasattr(self, 'scheduled_duration_agg'):
            return self.scheduled_duration_agg or 0
        elif hasattr(self, '_prefetched_objects_cache') and \
                'chunks' in self._prefetched_objects_cache:
            # aggregating in the prefetched chunks is more efficient than
            # another db access
            return Decimal(sum(
                chunk.duration
                for chunk in self.chunks.all()
            ))
        return self.chunks.aggregate(Sum('duration'))['duration__sum'] or Decimal(0)

    @property
    def unscheduled_duration(self) -> Decimal:
        """The duration which is not yet scheduled."""
        return self.duration - self.scheduled_duration

    @property
    def finished_duration(self) -> Decimal:
        if hasattr(self, 'finished_duration_agg'):
            return self.finished_duration_agg or 0
        elif hasattr(self, '_prefetched_objects_cache') and \
                'chunks' in self._prefetched_objects_cache:
            # aggregating in the prefetched chunks is more efficient than
            # another db access
            return Decimal(sum(
                chunk.duration
                for chunk in self.chunks.all()
                if chunk.finished
            ))
        return self.chunks.filter(finished=True).aggregate(
            Sum('duration'))['duration__sum'] or Decimal(0)

    @property
    def unfinished_duration(self) -> Decimal:
        return self.duration - self.finished_duration

    def get_day_for_scheduling(
            self, special_date: str, duration: Decimal) -> Union[None, date]:
        """
        Determine a day on which another chunk of this task can be scheduled
        based on a special day string (i.e., 'today' or 'next_free_capacity').
        """
        assert special_date in self.VALID_SCHEDULE_SPECIAL_DATES, 'unknown special_date value'

        if special_date == 'today':
            return date.today()
        elif special_date == 'tomorrow':
            return date.today() + timedelta(days=1)
        elif special_date == 'next_free_capacity':
            return TaskChunk.next_day_with_capacity(
                self.user, duration)


class TaskChunk(models.Model):
    """
    A chunk of a task that is scheduled for a specific day.
    """

    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name='chunks')
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
            self.day_order = TaskChunk.get_next_day_order(
                self.task.user, self.day)

    def __str__(self) -> str:
        return '{}: {}'.format(self.task, self.day)

    @transaction.atomic
    def delete(self, postpone: bool = True):
        """
        Delete this task chunk.

        When not postponed, the duration of the task is reduced by the
        duration of this task chunk.
        """
        if not postpone:
            # reduce the tasks duration

            # make sure this task is locked (on supported db backends)
            task = Task.objects.select_for_update().filter(pk=self.task_id).first()

            task.duration -= self.duration
            if task.duration <= 0:
                task.delete()
            else:
                task.save(update_fields=('duration',))
        super().delete()

    @transaction.atomic
    def split(self, duration: Decimal = 1) -> List['TaskChunk']:
        """
        Split this chunk into two, keeping duration for the first
        chunk and moving the rest into the new chunk.

        Returns a list of all task chunks that have been touched.
        """
        assert self.duration > duration
        assert not self.finished

        relevant_chunks = TaskChunk.objects.filter(
            task__user_id=self.task.user_id,
            day=self.day, day_order__gte=self.day_order).order_by(
            'day_order').select_for_update()

        # force evaluation of queryset
        relevant_chunks = list(relevant_chunks)

        new_chunk = TaskChunk.objects.create(
            task=self.task,
            day=self.day,
            day_order=self.day_order + 1,
            duration=self.duration - duration)
        self.duration = duration
        self.save(update_fields=('duration',))

        # update duration in relevant_chunks
        for chunk in relevant_chunks:
            if chunk.id == self.id:
                chunk.duration = self.duration

        # increase all future day orders
        for chunk in relevant_chunks:
            if chunk.pk == self.pk:
                continue
            chunk.day_order += 1
            chunk.save(update_fields=('day_order',))

        return [new_chunk] + relevant_chunks

    @staticmethod
    def get_next_day_order(user, day):
        """Get the next day order for a specific day."""
        return (TaskChunk.objects.filter(
            task__user=user,
            day=day).aggregate(Max('day_order'))['day_order__max'] or 0) + 1

    @staticmethod
    def missed_chunks(user: get_user_model()) -> QuerySet:
        """Get all unfinished task chunks scheduled for a past day."""
        return TaskChunk.objects.filter(
            task__user=user,
            day__lt=date.today(),
            finished=False
        ).order_by('day').select_related('task')

    @staticmethod
    def next_day_with_capacity(user: get_user_model(), min_remaining_capacity: Decimal,
                               max_days: int = 60) -> Union[date, None]:
        """
        Get the next day on which user has at least min_capacity of
        unscheduled duration left.
        """
        if min_remaining_capacity > user.workhours_weekday and min_remaining_capacity > user.workhours_weekend:
            # can not fit into a single day
            return None

        today = date.today()
        max_date = today + timedelta(days=max_days)

        # aggregate scheduled duration for the next days
        days = TaskChunk.objects.filter(
            task__user=user,
            day__gte=today,
            day__lt=max_date,
        ).values('day').annotate(
            scheduled_duration=Sum('duration'))
        days = {
            row['day']: row['scheduled_duration']
            for row in days
        }

        # search for the earliest day with enough remaining capacity
        day = today
        while day < max_date:
            total_capacity = user.capacity_of_day(day)
            scheduled_duration = days.get(day, 0)
            remaining_capacity = total_capacity - scheduled_duration

            if remaining_capacity > min_remaining_capacity:
                return day

            day += timedelta(days=1)

        return None

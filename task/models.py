from typing import List, Optional, Union

from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
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
        max_digits=8, decimal_places=2, default=1,
        validators=(
            MinValueValidator(Decimal('0.01')),
        ))

    priority = models.IntegerField(
        default=5, help_text='Value between 0 (lowest) and 10 (highest)',
        validators=(
            MinValueValidator(0),
            MaxValueValidator(10),
        ))

    start = models.DateField(null=True)
    deadline = models.DateField(null=True)

    labels = models.ManyToManyField('label.Label', related_name='tasks')

    notes = models.TextField(null=True)

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

    @transaction.atomic
    def merge(self, task: 'Task') -> List['TaskChunk']:
        """
        Merge task into this task.
        Returns all affected task chunks.
        """
        assert self.pk != task.pk
        assert task.user == self.user

        a, b = Task.objects.filter(pk__in=(self.pk, task.pk)).select_for_update()

        self.duration = a.duration + b.duration
        self.save(update_fields=('duration',))
        task.chunks.update(task_id=self.pk)
        task.delete()
        return TaskChunk.objects.filter(task_id__in=(self.pk, task.pk))


class TaskChunkSeries(models.Model):
    """
    Models a series of task chunks.
    They are used to schedule several task chunks at once.
    Infinitive task chunk series can be used to have a series of
    task chunks that continues to expand regularly.
    """
    class Meta:
        verbose_name_plural = 'task chunk series'

    RULE_CHOICES = (
        ('interval', 'schedule in an interval of a fixed number of days'),
        ('monthly', 'schedule on a specific day in an interval of a fixed number of months'),
        ('monthlyweekday', 'schedule on a specific weekday in an interval of a fixed number of months'),
    )

    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name='chunk_series')
    duration = models.DecimalField(
        max_digits=4, decimal_places=2, default=1,
        validators=(
            MinValueValidator(Decimal('0.01')),
        ))

    # the first day on which to schedule a chunk for this series
    start = models.DateField()
    # the last day on which a chunk may be scheduled; infinite series if null
    end = models.DateField(null=True)

    last_scheduled_day = models.DateField(null=True)
    completely_scheduled = models.BooleanField(default=False)

    rule = models.CharField(max_length=15, choices=RULE_CHOICES)

    # rule-specific parameters:

    interval_days = models.IntegerField(null=True, validators=(
        MinValueValidator(1),
    ))
    # the day of the month to schedule; if the month has fewer days than
    # the specified date, the last day of the month is used
    monthly_day = models.IntegerField(null=True, validators=(
        MinValueValidator(1), MaxValueValidator(31),
    ))
    monthly_months = models.IntegerField(null=True, validators=(
        MinValueValidator(1),
    ))
    # the weekday to schedule (0=mon, ..., 6=sunday)
    monthlyweekday_weekday = models.IntegerField(null=True, validators=(
        MinValueValidator(0), MaxValueValidator(6),
    ))
    # use the nth of the specified weekday of this month; if the month has
    # fewer than n instances of that weekday, use the last of that month
    monthlyweekday_nth = models.IntegerField(null=True, validators=(
        MinValueValidator(1), MaxValueValidator(6),
    ))

    def __str__(self) -> str:
        return '{}: {}'.format(self.task, self.rule)

    @transaction.atomic
    def schedule(
            self,
            max_count: int = 50,
            max_advance: timedelta = timedelta(days=365)) -> List['TaskChunk']:
        """
        Schedule (more) task chunks for this series.
        Creates at most max_count new instances and at most max_advance days
        into the future.
        """
        new_instances = []
        day = self.last_scheduled_day
        advance_base = date.today()
        for i in range(max_count):
            day = self.apply_rule(day)

            if day is None:
                # no further instance to schedule, complete now
                self.completely_scheduled = True
                self.save(update_fields=('completely_scheduled',))
                break

            if advance_base:
                advance = day - advance_base
                if advance > max_advance:
                    # reached limit for this schedule
                    break

            # TODO: find a way to determine the day order by a subquery
            # to prevent using a single query for each day
            # (or, at least, bundle the days and aggregate all day orders
            # at once)
            new_instances.append(
                TaskChunk(
                    task=self.task,
                    series=self,
                    day=day,
                    day_order=TaskChunk.get_next_day_order(self.task.user, day),
                    duration=self.duration,
                ))

        if new_instances:
            # create the new instances
            TaskChunk.objects.bulk_create(new_instances)
            self.last_scheduled_day = new_instances[-1].day
            self.save(update_fields=('last_scheduled_day',))

            # update the duration of the task
            self.task.duration = F('duration') + self.duration * len(new_instances)
            self.task.save(update_fields=('duration',))
            # refresh the task from the db to get the actual duration value
            self.task.refresh_from_db()

        return new_instances

    def apply_rule(self, last: Optional[date] = None) -> Optional[date]:
        """
        Apply the rule of this task chunk series.
        Finds the date on which the next occurrence should be scheduled
        when the last was scheduled on the provided date.
        If no last day is specified, the start date of this series is used.

        If no further occurrence is to be scheduled, None is returned.
        """
        if last and last < self.start:
            # if the start date is modified after chunks are scheduled
            # already, prevent from scheduling any more chunks in the
            # past
            last = None

        apply = getattr(self, '_apply_{}'.format(self.rule), None)
        assert apply, 'invalid rule %s' % self.rule
        next = apply(last)

        if self.end and next > self.end:
            return None

        return next

    def _apply_interval(self, last: Optional[date]) -> Optional[date]:
        assert self.interval_days

        if not last:
            return self.start
        return last + timedelta(days=self.interval_days)

    def _apply_monthly(self, last: Optional[date], day: Optional[int] = None) -> Optional[date]:
        assert self.monthly_day or day
        assert self.monthly_months

        if not day:
            day = self.monthly_day

        if not last:
            return self._replace_day(self.start, day)

        next = self._add_months(last, self.monthly_months)
        return self._replace_day(next, day)

    def _apply_monthlyweekday(self, last: Optional[date]) -> Optional[date]:
        assert self.monthly_months
        assert self.monthlyweekday_weekday
        assert self.monthlyweekday_nth

        next = self._apply_monthly(last, 1)

        next = self._advance_to_weekday(next, self.monthlyweekday_weekday)
        desired_month = next.month
        for shift in range(self.monthlyweekday_nth - 1):
            shifted = next + timedelta(days=7)
            if shifted.month != desired_month:
                # use last weekday of this month
                break
            next = shifted

        return next

    @staticmethod
    def _add_months(day: date, months: int) -> date:
        """
        Add months to a date without changing the day.
        """
        new_month = day.month + months - 1
        return day.replace(
            month=(new_month % 12) + 1,
            year=day.year + new_month // 12)

    @staticmethod
    def _advance_to_weekday(day: date, weekday: int) -> date:
        """
        Advance a date object until it reaches weekday, leaving it
        untouched if it is already the right weekday.
        """
        while day.weekday() != weekday:
            day += timedelta(days=1)
        return day

    @staticmethod
    def _replace_day(day: date, replace: int) -> date:
        """
        Replace the day of the date, using the last day
        of the month if it is out of range.
        """
        try:
            return day.replace(day=replace)
        except ValueError:
            # get the last day of this month
            day = TaskChunkSeries._add_months(day, 1).replace(day=1)
            return day - timedelta(days=1)


class TaskChunk(models.Model):
    """
    A chunk of a task that is scheduled for a specific day.
    """

    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name='chunks')
    series = models.ForeignKey(
        TaskChunkSeries, on_delete=models.SET_NULL, related_name='chunks',
        null=True)
    day = models.DateField()
    day_order = models.SmallIntegerField()
    duration = models.DecimalField(
        max_digits=4, decimal_places=2, default=1,
        validators=(
            MinValueValidator(Decimal('0.01')),
        ))
    finished = models.BooleanField(default=False)

    notes = models.TextField(null=True)

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

            if remaining_capacity >= min_remaining_capacity:
                return day

            day += timedelta(days=1)

        return None

from datetime import date, timedelta

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST

from .forms import TaskForm, ScheduleForm
from .models import Task, TaskExecution


@require_POST
@login_required
def create_task(
        request: HttpRequest) -> HttpResponse:
    """Create a new task."""
    form = TaskForm(request.POST)
    if not form.is_valid():
        messages.warning(
            request, _('The task is invalid'))
        return redirect('task:overview')
    form.instance.user = request.user
    form.save()
    messages.success(
        request, _('The task "%s" was created successfully.') % (form.instance.name,))
    return redirect('task:overview')


# TODO (security): This should use POST!
@login_required
def change_task_execution_duration(
        request: HttpRequest,
        task_execution_pk: int, seconds_delta: int) -> HttpResponse:
    """Add/remove time from an execution and its event."""
    task_execution = get_object_or_404(
        TaskExecution.objects.filter(task__user=request.user).select_related('task'),
        pk=task_execution_pk)
    with transaction.atomic():
        task_execution.duration += Decimal(seconds_delta) / 3600
        task_execution.task.estimated_duration += Decimal(seconds_delta) / 3600
        if task_execution.duration <= 0 or task_execution.task.estimated_duration <= 0:
            messages.warning(request, _('The duration is too low.'))
            return redirect('task:overview')
        task_execution.save(update_fields=('duration',))
        task_execution.task.save(update_fields=('estimated_duration',))
    return redirect('task:overview')


# TODO (security): This should use POST!
@login_required
def delete_task_execution(
        request: HttpRequest,
        task_execution_pk: int) -> HttpResponse:
    """Add/remove time from an execution and its event."""
    task_execution = get_object_or_404(
        TaskExecution.objects.filter(task__user=request.user).select_related('task'),
        pk=task_execution_pk)
    with transaction.atomic():
        task = task_execution.task
        task.estimated_duration -= task_execution.duration
        if task.estimated_duration <= 0:
            task.delete()
        else:
            task.save(update_fields=('estimated_duration',))
        task_execution.delete()
        messages.success(request, _('The task execution has been deleted successfully.'))
    return redirect('task:overview')


# TODO (security): This should use POST!
@login_required
def finish_task_execution(
        request: HttpRequest,
        task_execution_pk: int, finished: str) -> HttpResponse:
    """Finish/unfinish a task execution."""
    task_execution = get_object_or_404(
        TaskExecution.objects.filter(task__user=request.user).select_related('task'),
        pk=task_execution_pk)
    finished = finished == 'yes'
    task_execution.finished = finished
    task_execution.save(update_fields=('finished',))
    return redirect('task:overview')


# TODO (security): This should use POST!
@login_required
def move_task_execution(
        request: HttpRequest,
        task_execution_pk: int, direction: str) -> HttpResponse:
    """Add/remove time from an execution and its event."""
    task_execution = get_object_or_404(
        TaskExecution.objects.filter(task__user=request.user),
        pk=task_execution_pk)
    exchange = TaskExecution.objects.filter(task__user=request.user).filter(
        day=task_execution.day, finished=task_execution.finished)
    if direction == 'up':
        exchange = exchange.filter(day_order__lt=task_execution.day_order).order_by(
            '-day_order')
        error_msg = _('The task is already the earliest.')
    else:
        exchange = exchange.filter(day_order__gt=task_execution.day_order).order_by(
            'day_order')
        error_msg = _('The task is already the last.')
    exchange = exchange.first()
    if not exchange:
        messages.warning(request, error_msg)
        return redirect('task:overview')

    with transaction.atomic():
        task_execution.day_order,  exchange.day_order = exchange.day_order, \
                                                        task_execution.day_order
        task_execution.save(update_fields=('day_order',))
        exchange.save(update_fields=('day_order',))
    return redirect('task:overview')


# TODO (security): This should use POST!
@login_required
def postpone_task_execution(
        request: HttpRequest,
        task_execution_pk: int) -> HttpResponse:
    """Remove a task execution to postpone it."""
    task_execution = get_object_or_404(
        TaskExecution.objects.filter(task__user=request.user),
        pk=task_execution_pk)
    task_execution.delete()
    messages.success(request, _('The task was postponed successfully.'))
    return redirect('task:overview')


# TODO (security): This should use POST!
@login_required
def reserve_task_time(
        request: HttpRequest,
        task_pk: int, seconds: int) -> HttpResponse:
    task = get_object_or_404(request.user.tasks, pk=task_pk)
    task.estimated_duration = F('estimated_duration') + Decimal(seconds) / 3600
    task.save(update_fields=('estimated_duration',))
    return redirect('task:overview')


@require_POST
@login_required
def schedule_task(
        request: HttpRequest) -> HttpResponse:
    """Reserve time for future scheduling."""
    form = ScheduleForm(request.POST)
    if not form.is_valid():
        messages.warning(request, _('Schedule is invalid.'))
        return redirect('task:overview')

    task = get_object_or_404(
        request.user.tasks,
        pk=form.cleaned_data.get('task_id'))
    duration = form.cleaned_data.get('duration')
    schedule_for = form.cleaned_data.get('schedule_for')
    schedule_for_date = form.cleaned_data.get('schedule_for_date')
    with transaction.atomic():
        if duration > task.unscheduled_duration:
            messages.warning(
                request, _(
                    'The scheduled duration is greater than the unscheduled task duration. '
                    'The task duration is increased.'))
            task.estimated_duration += duration - task.unscheduled_duration
        scheduled_day = task.schedule(schedule_for, schedule_for_date, duration)
        if not scheduled_day:
            if schedule_for == 'next_free_capacity':
                messages.warning(
                    request,
                    _('No capacity has been found in the near future.'))
            else:
                messages.warning(
                    request,
                    _('The chosen day has too less capacities.'))
            return redirect('task:overview')
        # if duration has been increased
        task.save()
        messages.success(
            request,
            _('The task was scheduled successfully for %s.') % scheduled_day)

    return redirect('task:overview')


@login_required
def overview(request: HttpRequest) -> HttpResponse:
    """Overview."""
    return render(request, 'task/overview.html', {
        'schedule_form': ScheduleForm(),
        'schedule_by_day': TaskExecution.schedule_by_day(
            request.user, date.today() - timedelta(days=1), 7),
        'task_form': TaskForm(),
        'unscheduled_tasks': Task.unscheduled_tasks(request.user),
    })

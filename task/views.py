from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .models import Task, TaskExecution


@login_required
def overview(request: HttpRequest) -> HttpResponse:
    """Overview."""
    return render(request, 'task/overview.html', {
        'unscheduled_tasks': Task.unscheduled_tasks(request.user),
        'schedule_by_day': TaskExecution.schedule_by_day(
            request.user, date.today() - timedelta(days=1), 4),
    })

from datetime import date

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from task.models import Task, TaskExecution
from task.serializers import TaskSerializer, DaySerializer


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def unscheduled_tasks(request: Request) -> Response:
    """Get all tasks that are not fully scheduled."""
    tasks = Task.unscheduled_tasks(request.user)
    return Response({
        'unscheduled_tasks': TaskSerializer(tasks, many=True).data,
    })


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def scheduled_tasks(request: Request) -> Response:
    """Get all tasks that are not fully scheduled."""
    first_day = request.query_params.get('first_day', date.today())
    days = request.query_params.get('days', 7)
    return Response({
        'scheduled_tasks': DaySerializer(
            list(TaskExecution.schedule_by_day(request.user, first_day, days)),
            many=True).data,
    })

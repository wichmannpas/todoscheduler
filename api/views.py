from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from task.models import Task
from task.serializers import TaskSerializer


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def unscheduled_tasks(request: Request) -> Response:
    """Get all tasks that are not fully scheduled."""
    tasks = Task.unscheduled_tasks(request.user)
    return Response({
        'unscheduled_tasks': TaskSerializer(tasks, many=True).data,
    })

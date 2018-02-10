from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(
    r'task',
    views.TaskViewSet,
    base_name='task')
router.register(
    r'taskexecution',
    views.TaskExecutionViewSet,
    base_name='task_execution')

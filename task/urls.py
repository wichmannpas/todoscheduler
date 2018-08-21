from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register(
    'task',
    views.TaskViewSet,
    base_name='task')
router.register(
    'taskexecution',
    views.TaskExecutionViewSet,
    base_name='task_execution')
urlpatterns = router.urls

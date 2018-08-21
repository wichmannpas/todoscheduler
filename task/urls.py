from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register(
    'task',
    views.TaskViewSet,
    base_name='task')
router.register(
    'chunk',
    views.TaskChunkViewSet,
    base_name='chunk')
urlpatterns = router.urls

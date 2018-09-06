from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register(
    'task',
    views.TaskViewSet,
    base_name='task')
router.register(
    'chunk/series',
    views.TaskChunkSeriesViewSet,
    base_name='taskchunkseries')
router.register(
    'chunk',
    views.TaskChunkViewSet,
    base_name='taskchunk')
urlpatterns = router.urls

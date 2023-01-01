from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register(
    'task',
    views.TaskViewSet,
    basename='task')
router.register(
    'chunk/series',
    views.TaskChunkSeriesViewSet,
    basename='taskchunkseries')
router.register(
    'chunk',
    views.TaskChunkViewSet,
    basename='taskchunk')
urlpatterns = router.urls

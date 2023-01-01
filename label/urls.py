from rest_framework.routers import SimpleRouter

from . import views

app_name = 'label'

router = SimpleRouter()
router.register(
    'label',
    views.LabelViewSet,
    basename='label')
urlpatterns = router.urls

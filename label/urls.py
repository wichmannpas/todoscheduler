from rest_framework.routers import SimpleRouter

from . import views

app_name = 'label'

router = SimpleRouter()
router.register(
    'label',
    views.LabelViewSet,
    base_name='label')
urlpatterns = router.urls

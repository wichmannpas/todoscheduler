from rest_framework.routers import SimpleRouter

from . import views


app_name = 'base'

router = SimpleRouter()
router.register(
    'user',
    views.UserViewSet)
urlpatterns = router.urls

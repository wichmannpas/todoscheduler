from django.conf.urls import include, url
from rest_framework.authtoken import views as authtoken_views

from base.views import UserView
from task.routers import router as task_router

app_name = 'api'
urlpatterns = [
    url(r'^token-auth/', authtoken_views.obtain_auth_token),
    url(r'^user/', UserView().as_view()),
    url(r'^tasks/', include(task_router.urls)),
]

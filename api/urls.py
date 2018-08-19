from django.conf.urls import include, url

from base.views import UserView
from task.routers import router as task_router

app_name = 'api'
urlpatterns = [
    url(r'^user/', UserView().as_view()),
    url(r'^tasks/', include(task_router.urls)),
]

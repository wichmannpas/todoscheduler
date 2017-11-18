from django.conf.urls import url
from rest_framework.authtoken import views as authtoken_views

from . import views

app_name = 'api'
urlpatterns = [
    url(r'^token-auth/', authtoken_views.obtain_auth_token),
    url(r'^tasks/unscheduled/', views.unscheduled_tasks, name='unscheduled_tasks'),
    url(r'^tasks/scheduled/', views.scheduled_tasks, name='scheduled_tasks'),
]

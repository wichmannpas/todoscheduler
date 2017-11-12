from django.conf.urls import url

from . import views

app_name = 'task'
urlpatterns = [
    url(r'^$', views.overview, name='overview'),
    url(r'^execution/(?P<task_execution_pk>\d+)/delete/$',
        views.delete_task_execution, name='delete_task_execution'),
    url(r'^execution/(?P<task_execution_pk>\d+)/duration/change/(?P<seconds_delta>-?(\d+))/$',
        views.change_task_execution_duration, name='change_task_execution_duration'),
    url(r'^execution/(?P<task_execution_pk>\d+)/finished/(?P<finished>(yes|no))/$',
        views.finish_task_execution, name='finish_task_execution'),
    url(r'^execution/(?P<task_execution_pk>\d+)/move/(?P<direction>(up|down))/$',
        views.move_task_execution, name='move_task_execution'),
    url(r'^execution/(?P<task_execution_pk>\d+)/postpone/$',
        views.postpone_task_execution, name='postpone_task_execution'),
    url(r'^task/(?P<task_pk>\d+)/reserve/(?P<seconds>\d+)/$',
        views.reserve_task_time, name='reserve_task_time'),
    url(r'^task/create/$',
        views.create_task, name='create_task'),
    url(r'^task/schedule/$',
        views.schedule_task, name='schedule_task'),
]

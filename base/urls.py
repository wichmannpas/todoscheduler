from django.conf.urls import url

from . import views

app_name = 'base'
urlpatterns = [
    url(r'^imprint/$', views.imprint, name='imprint'),
]

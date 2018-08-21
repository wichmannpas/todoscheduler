from django.urls import path

from . import views


app_name = 'base'

urlpatterns = [
    path('user/', views.UserView.as_view()),
]

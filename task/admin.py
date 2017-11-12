from django.contrib import admin

from .models import Task, TaskExecution


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'estimated_duration',
        'user',
    )


@admin.register(TaskExecution)
class TaskExecutionAdmin(admin.ModelAdmin):
    list_display = (
        'day',
        'duration',
        'task',
    )

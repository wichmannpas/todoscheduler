from django.contrib import admin

from .models import Task, TaskChunk, TaskChunkSeries


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'duration',
        'user',
    )


@admin.register(TaskChunk)
class TaskChunkAdmin(admin.ModelAdmin):
    list_display = (
        'day',
        'duration',
        'task',
    )


@admin.register(TaskChunkSeries)
class TaskChunkSeriesAdmin(admin.ModelAdmin):
    list_display = (
        'task',
        'duration',
    )

from django.contrib import admin

from .models import Label


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'title',
        'color',
    )

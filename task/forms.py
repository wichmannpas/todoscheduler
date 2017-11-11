from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import Task


class ScheduleForm(forms.Form):
    schedule_for = forms.ChoiceField(
        label=_('Schedule for'),
        choices=(
        ('today', _('Today')),
        ('tomorrow', _('Tomorrow')),
        ('next_free_capacity', _('Next Free Capacity')),
        ('another_time', _('Another Time')),
    ))
    duration = forms.DecimalField(
        label=_('Duration'),
        max_digits=4, decimal_places=2)
    task_id = forms.IntegerField(widget=forms.HiddenInput())


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = (
            'name',
            'estimated_duration',
        )

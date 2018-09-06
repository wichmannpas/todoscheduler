from django.core.management import BaseCommand

from task.models import TaskChunkSeries


class Command(BaseCommand):
    def handle(self, **arguments):
        incomplete_series = TaskChunkSeries.objects.filter(
            completely_scheduled=False)
        chunk_count = 0
        for series in incomplete_series:
            chunk_count += len(series.schedule())
        self.stdout.write(
            'scheduled {} chunks for {} series\n'.format(
                chunk_count, len(incomplete_series)))

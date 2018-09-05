# Generated by Django 2.1 on 2018-09-05 10:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0011_taskchunkseries'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskchunk',
            name='series',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chunks', to='task.TaskChunkSeries'),
        ),
    ]

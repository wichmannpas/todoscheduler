# Generated by Django 2.1 on 2018-09-10 17:00

from decimal import Decimal
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0012_auto_20180907_1657'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='duration',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))]),
        ),
    ]

# Generated by Django 2.0 on 2018-02-03 10:22

from decimal import Decimal
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0003_auto_20171116_1505'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='duration',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))]),
        ),
    ]

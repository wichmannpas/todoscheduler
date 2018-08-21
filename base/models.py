from datetime import date
from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models


class User(AbstractUser):
    workhours_weekday = models.DecimalField(
        max_digits=4, decimal_places=2, default=8,
        validators=[MinValueValidator(0)])
    workhours_weekend = models.DecimalField(
        max_digits=4, decimal_places=2, default=4,
        validators=[MinValueValidator(0)])

    default_schedule_duration = models.DecimalField(
        max_digits=4, decimal_places=2, default=1,
        validators=[MinValueValidator(0)])
    default_schedule_full_duration_max = models.DecimalField(
        max_digits=4, decimal_places=2, default=3,
        validators=[MinValueValidator(0)])

    def capacity_of_day(self, day: date) -> Decimal:
        if day.weekday() < 5:
            return self.workhours_weekday

        return self.workhours_weekend

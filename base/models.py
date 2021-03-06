from datetime import date
from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class User(AbstractUser):
    workhours_weekday = models.DecimalField(
        max_digits=4, decimal_places=2, default=8,
        validators=(
            MinValueValidator(0),
            MaxValueValidator(24)))
    workhours_weekend = models.DecimalField(
        max_digits=4, decimal_places=2, default=4,
        validators=(
            MinValueValidator(0),
            MaxValueValidator(24)))

    default_schedule_duration = models.DecimalField(
        max_digits=4, decimal_places=2, default=1,
        validators=(
            MinValueValidator(0),
            MaxValueValidator(24)))
    default_schedule_full_duration_max = models.DecimalField(
        max_digits=4, decimal_places=2, default=3,
        validators=(
            MinValueValidator(0),
            MaxValueValidator(24)))

    def capacity_of_day(self, day: date) -> Decimal:
        if day.weekday() < 5:
            return self.workhours_weekday

        return self.workhours_weekend

    def __str__(self) -> str:
        return self.username

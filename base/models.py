from django.db import models


from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    workhours_weekday = models.DecimalField(
        max_digits=4, decimal_places=2, default=8)
    workhours_weekend = models.DecimalField(
        max_digits=4, decimal_places=2, default=4)

from django.db import models

from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _

class User(AbstractUser):
    email = models.EmailField(_('email address'), blank=True, unique=True)

    workhours_weekday = models.DecimalField(
        max_digits=4, decimal_places=2, default=8)
    workhours_weekend = models.DecimalField(
        max_digits=4, decimal_places=2, default=4)

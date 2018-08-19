from base64 import urlsafe_b64encode
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_authtoken.models import AuthToken
from rest_framework.test import APIClient


class AuthenticatedApiTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(
            username='johndoe',
            email='a',
            workhours_weekday=Decimal(10),
            workhours_weekend=Decimal(5),
            default_schedule_duration=Decimal(1),
            default_schedule_full_duration_max=Decimal(3),
        )
        self.user.set_password('foobar123')
        self.user.save()
        token = urlsafe_b64encode(AuthToken.create_token_for_user(self.user)).decode()

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token {}'.format(token))

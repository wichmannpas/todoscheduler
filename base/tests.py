from base64 import urlsafe_b64encode
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_authtoken.models import AuthToken
from rest_framework.test import APIClient

from .models import User


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


class UserTest(TestCase):
    def test_day_capacity(self):
        """
        Test that the correct capacity of a day is returned based on
        whether it is a weekday or not.
        """
        user = User(
            workhours_weekday=Decimal(8),
            workhours_weekend=Decimal(4)
        )

        monday = date(2018, 8, 20)
        tuesday = date(2018, 8, 21)
        wednesday = date(2018, 8, 22)
        thursday = date(2018, 8, 23)
        friday = date(2018, 8, 24)
        saturday = date(2018, 8, 25)
        sunday = date(2018, 8, 26)

        self.assertEqual(
            user.capacity_of_day(monday),
            Decimal(8))
        self.assertEqual(
            user.capacity_of_day(tuesday),
            Decimal(8))
        self.assertEqual(
            user.capacity_of_day(wednesday),
            Decimal(8))
        self.assertEqual(
            user.capacity_of_day(thursday),
            Decimal(8))
        self.assertEqual(
            user.capacity_of_day(friday),
            Decimal(8))
        self.assertEqual(
            user.capacity_of_day(saturday),
            Decimal(4))
        self.assertEqual(
            user.capacity_of_day(sunday),
            Decimal(4))

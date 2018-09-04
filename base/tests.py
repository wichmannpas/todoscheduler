from base64 import urlsafe_b64encode
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model, authenticate
from django.test import TestCase
from rest_authtoken.models import AuthToken
from rest_framework import status
from rest_framework.test import APIClient

from .models import User


class AuthenticatedApiTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(
            username='johndoe',
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


class UserViewTest(AuthenticatedApiTest):
    def test_retrieve_user(self):
        resp = self.client.get('/base/user/')
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            resp.data['username'],
            self.user.username)
        self.assertEqual(
            Decimal(resp.data['workhours_weekday']),
            self.user.workhours_weekday)
        self.assertEqual(
            Decimal(resp.data['workhours_weekend']),
            self.user.workhours_weekend)
        self.assertEqual(
            Decimal(resp.data['default_schedule_duration']),
            self.user.default_schedule_duration)
        self.assertEqual(
            Decimal(resp.data['default_schedule_full_duration_max']),
            self.user.default_schedule_full_duration_max)

    def test_update_user(self):
        resp = self.client.patch('/base/user/', {
            'workhours_weekday': 3,
            'workhours_weekend': 1,
            'default_schedule_duration': '0.5',
            'default_schedule_full_duration_max': 2,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.user.refresh_from_db()

        self.assertEqual(
            Decimal(resp.data['workhours_weekday']),
            Decimal(3))
        self.assertEqual(
            Decimal(resp.data['workhours_weekday']),
            self.user.workhours_weekday)

        self.assertEqual(
            Decimal(resp.data['workhours_weekend']),
            Decimal(1))
        self.assertEqual(
            Decimal(resp.data['workhours_weekend']),
            self.user.workhours_weekend)

        self.assertEqual(
            Decimal(resp.data['default_schedule_duration']),
            Decimal('0.5'))
        self.assertEqual(
            Decimal(resp.data['default_schedule_duration']),
            self.user.default_schedule_duration)

        self.assertEqual(
            Decimal(resp.data['default_schedule_full_duration_max']),
            Decimal(2))
        self.assertEqual(
            Decimal(resp.data['default_schedule_full_duration_max']),
            self.user.default_schedule_full_duration_max)

    def test_update_username(self):
        """
        Ensure that it is not allowed to change the username.
        """
        self.client.patch('/base/user/', {
            'username': 'foobar',
        })
        self.user.refresh_from_db()
        self.assertNotEqual(
            self.user.username,
            'foobar')

    def test_update_user_invalid_data(self):
        """
        Ensure that it is not allowed to set the user settings to
        invalid values.
        """
        resp = self.client.patch('/base/user/', {
            'workhours_weekday': -3,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)

        resp = self.client.patch('/base/user/', {
            'workhours_weekend': -5,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)

        resp = self.client.patch('/base/user/', {
            'default_schedule_duration': -5,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)

        resp = self.client.patch('/base/user/', {
            'default_schedule_full_duration_max': -37,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)

        resp = self.client.patch('/base/user/', {
            'workhours_weekday': 25,  # more than a single day
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)

        resp = self.client.patch('/base/user/', {
            'workhours_weekend': 25,  # more than a single day
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)

        resp = self.client.patch('/base/user/', {
            'default_schedule_duration': 25,  # more than a single day
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)

        resp = self.client.patch('/base/user/', {
            'default_schedule_full_duration_max': 25,  # more than a single day
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)

    def test_update_password(self):
        """
        Ensure that it is not allowed to set the user settings to
        invalid values.
        """
        self.assertIsNone(
            authenticate(username=self.user.username, password='changedpassword'))
        resp = self.client.patch('/base/user/', {
            'password': 'changedpassword',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            authenticate(username=self.user.username, password='changedpassword'),
            self.user)

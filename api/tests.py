"""
The api tests only test that the api is returning the requested data.
The contained data needs to be tested in the apps which generate it (i.e. api-independent)
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APIClient


class ApiTest(TestCase):
    fixtures = ['user-data.json']

    def setUp(self):
        self.user = get_user_model().objects.get(username='admin')
        self.client = APIClient()
        self.client.login(username='admin', password='foobar123')

    def test_scheduled_tasks(self):
        response = self.client.get(reverse('api:scheduled_tasks'), format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertIn('scheduled_tasks', response.data)

    def test_unscheduled_tasks(self):
        response = self.client.get(reverse('api:unscheduled_tasks'), format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertIn('unscheduled_tasks', response.data)

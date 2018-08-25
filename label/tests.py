from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status

from base.tests import AuthenticatedApiTest
from .models import Label


class LabelTest(TestCase):
    def setUp(self):
        self.user1 = get_user_model().objects.create(
            username='johndoe',
        )

    def test_str(self):
        label = Label(user=self.user1, title='Testlabel')
        self.assertEqual(
            str(label),
            'johndoe: Testlabel')


class LabelViewTest(AuthenticatedApiTest):
    def test_create_label(self):
        """
        Test the creation of a new label.
        """
        resp = self.client.post('/label/label/', {
            'title': 'Test Label',
            'description': 'A label description.',
            'color': '000000',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)

        self.assertEqual(
            Label.objects.count(),
            1)

        label = Label.objects.first()
        self.assertEqual(
            label.user,
            self.user)
        self.assertEqual(
            label.title,
            'Test Label')
        self.assertEqual(
            label.description,
            'A label description.')
        self.assertEqual(
            label.color,
            '000000')

    def test_create_label_invalid_color(self):
        resp = self.client.post('/label/label/', {
            'title': 'Test Label',
            'description': 'A label description.',
            'color': 'XZY123',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {
                'color',
            })
        self.assertEqual(
            Label.objects.count(),
            0)

        resp = self.client.post('/label/label/', {
            'title': 'Test Label',
            'description': 'A label description.',
            'color': '',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {
                'color',
            })
        self.assertEqual(
            Label.objects.count(),
            0)

    def test_create_label_color_normalization(self):
        resp = self.client.post('/label/label/', {
            'title': 'Test Label',
            'description': 'A label description.',
            'color': 'F1F1FC',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        label = Label.objects.first()
        self.assertEqual(
            label.color,
            'f1f1fc')

        resp = self.client.post('/label/label/', {
            'title': 'Test Label',
            'description': 'A label description.',
            'color': 'f1f1fc',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        label = Label.objects.first()
        self.assertEqual(
            label.color,
            'f1f1fc')

    def test_update_label(self):
        """
        Test the update of an existing label using both
        POST and PATCH.
        """
        label = Label.objects.create(
            user=self.user,
            title='Test Label',
            color='111111')
        resp = self.client.patch('/label/label/{}/'.format(label.id), {
            'title': 'Renamed label',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        label.refresh_from_db()
        self.assertEqual(
            label.title,
            'Renamed label')

        resp = self.client.put('/label/label/{}/'.format(label.id), {
            'title': 'Renamed label',
            'description': 'a long description of this label.',
            'color': '424242',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        label.refresh_from_db()
        self.assertEqual(
            label.title,
            'Renamed label')
        self.assertEqual(
            label.color,
            '424242')
        self.assertEqual(
            label.description,
            'a long description of this label.')

    def test_update_label_invalid_color(self):
        label = Label.objects.create(
            user=self.user,
            title='Test Label',
            color='111111')
        resp = self.client.patch('/label/label/{}/'.format(label.id), {
            'color': 'no valid color',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {
                'color',
            })
        label.refresh_from_db()
        self.assertEqual(
            label.color,
            '111111')

        label = Label.objects.create(
            user=self.user,
            title='Test Label',
            color='111111')
        resp = self.client.patch('/label/label/{}/'.format(label.id), {
            'color': 'ZZZZ11',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {
                'color',
            })
        label.refresh_from_db()
        self.assertEqual(
            label.color,
            '111111')

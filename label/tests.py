from django.contrib.auth import get_user_model
from django.test import TestCase

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

from django.contrib.sessions.models import Session

from base.selenium_test import SeleniumTest


class AccountTest(SeleniumTest):
    fixtures = ['user-data.json']

    def test_login(self):
        self.assertEqual(Session.objects.count(), 0)

        self.selenium.get(self.live_server_url)
        username_input = self.selenium.find_element_by_id("id_username")
        username_input.send_keys('admin')
        password_input = self.selenium.find_element_by_id("id_password")
        password_input.send_keys('foobar123')
        self.selenium.find_element_by_xpath('//input[@value="Login"]').click()

        self.assertEqual(Session.objects.count(), 1)

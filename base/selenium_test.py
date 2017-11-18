from subprocess import call, DEVNULL

from django.contrib.auth import get_user_model
from django.test.testcases import LiveServerTestCase
from selenium import webdriver


class SeleniumTest(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        # TODO: find a better way for static file handling compatible with django-pipeline
        call([
            './manage.py',
            'collectstatic',
            '--no-input'
        ], stdout=DEVNULL)
        super().setUpClass()
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        cls.selenium = webdriver.Chrome(chrome_options=options)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()


class AuthenticatedSeleniumTest(SeleniumTest):
    def setUp(self):
        self.selenium.get(self.live_server_url)
        username_input = self.selenium.find_element_by_id("id_username")
        username_input.send_keys('admin')
        password_input = self.selenium.find_element_by_id("id_password")
        password_input.send_keys('foobar123')
        self.selenium.find_element_by_xpath('//input[@value="Login"]').click()
        self.user = get_user_model().objects.get(username='admin')

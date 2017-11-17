from django.test.testcases import LiveServerTestCase
from selenium import webdriver


class SeleniumTest(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        cls.selenium = webdriver.Chrome(chrome_options=options)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

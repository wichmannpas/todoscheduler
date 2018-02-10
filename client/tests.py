from django.test import TestCase
from selenium.webdriver.support.ui import Select

from base.selenium_test import AuthenticatedSeleniumTest


class OverviewTest(AuthenticatedSeleniumTest):
    fixtures = ['user-data.json']

    def test_new_task(self):
        self.assertEqual(Task.objects.count(), 0)

        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_id('new_task_link').click()
        name_input = self.selenium.find_element_by_id('new_task_name')
        name_input.send_keys('Testtask')
        duration_input = self.selenium.find_element_by_id('id_duration')
        duration_input.clear()
        duration_input.send_keys('42.2')
        self.selenium.find_element_by_xpath('//input[@value="Create Task"]').click()

        self.assertEqual(Task.objects.count(), 1)
        task = Task.objects.first()
        self.assertEqual(task.name, 'Testtask')
        self.assertEqual(task.duration, Decimal('42.2'))

    def test_new_task_invalid_duration(self):
        self.assertEqual(Task.objects.count(), 0)

        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_id('new_task_link').click()
        name_input = self.selenium.find_element_by_id('new_task_name')
        name_input.send_keys('Testtask')
        duration_input = self.selenium.find_element_by_id('id_duration')
        duration_input.clear()
        duration_input.send_keys('-42.2')  # invalid value!
        self.selenium.find_element_by_xpath('//input[@value="Create Task"]').click()

        self.assertEqual(Task.objects.count(), 0)

    def test_edit_task_duration_too_low(self):
        """
        Test that it is not possible to set the total duration of a task
        to a value lower than the duration that is already scheduled.
        """
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=5)
        TaskExecution.objects.create(
            day=date.today(),
            task=task,
            duration=2,
            day_order=0)
        TaskExecution.objects.create(
            day=date.today(),
            task=task,
            duration=1,
            day_order=0,
            finished=True)

        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_class_name('task-edit').click()
        scheduled_display = self.selenium.find_element_by_id('edit_task_scheduled')
        self.assertEqual(
            scheduled_display.get_attribute('innerHTML'),
            '3')
        finished_display = self.selenium.find_element_by_id('edit_task_finished')
        self.assertEqual(
            finished_display.get_attribute('innerHTML'),
            '1')
        duration_input = self.selenium.find_element_by_id('edit_task_duration')
        duration_input.clear()
        duration_input.send_keys('1')  # invalid, 3 hours are already scheduled
        self.selenium.find_element_by_xpath('//input[@value="Update Task"]').click()

        self.assertIn(
            'The task is invalid',
            self.selenium.page_source)

        task.refresh_from_db()
        # the duration was not changed
        self.assertEqual(
            task.duration,
            Decimal(5))

    def test_edit_task_duration_unscheduled(self):
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=5)
        TaskExecution.objects.create(
            day=date.today(),
            task=task,
            duration=2,
            day_order=0)
        TaskExecution.objects.create(
            day=date.today(),
            task=task,
            duration=1,
            day_order=0,
            finished=True)

        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_class_name('task-edit').click()
        scheduled_display = self.selenium.find_element_by_id('edit_task_scheduled')
        self.assertEqual(
            scheduled_display.get_attribute('innerHTML'),
            '3')
        finished_display = self.selenium.find_element_by_id('edit_task_finished')
        self.assertEqual(
            finished_display.get_attribute('innerHTML'),
            '1')
        duration_input = self.selenium.find_element_by_id('edit_task_duration')
        duration_input.clear()
        duration_input.send_keys('42')
        self.selenium.find_element_by_xpath('//input[@value="Update Task"]').click()

        task.refresh_from_db()
        self.assertEqual(
            task.name,
            'Testtask')
        self.assertEqual(
            task.duration,
            Decimal(42))

    def test_edit_task_name_unscheduled(self):
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=5)
        TaskExecution.objects.create(
            day=date.today(),
            task=task,
            duration=2,
            day_order=0)
        TaskExecution.objects.create(
            day=date.today(),
            task=task,
            duration=1,
            day_order=0,
            finished=True)

        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_class_name('task-edit').click()
        scheduled_display = self.selenium.find_element_by_id('edit_task_scheduled')
        self.assertEqual(
            scheduled_display.get_attribute('innerHTML'),
            '3')
        finished_display = self.selenium.find_element_by_id('edit_task_finished')
        self.assertEqual(
            finished_display.get_attribute('innerHTML'),
            '1')
        name_input = self.selenium.find_element_by_id('edit_task_name')
        name_input.clear()
        name_input.send_keys('Edited Task')
        self.selenium.find_element_by_xpath('//input[@value="Update Task"]').click()

        task.refresh_from_db()
        self.assertEqual(
            task.name,
            'Edited Task')
        self.assertEqual(
            task.duration,
            Decimal(5))

    def test_edit_task_name_duration_unscheduled(self):
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=5)
        TaskExecution.objects.create(
            day=date.today(),
            task=task,
            duration=2,
            day_order=0)
        TaskExecution.objects.create(
            day=date.today(),
            task=task,
            duration=1,
            day_order=0,
            finished=True)

        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_class_name('task-edit').click()
        scheduled_display = self.selenium.find_element_by_id('edit_task_scheduled')
        self.assertEqual(
            scheduled_display.get_attribute('innerHTML'),
            '3')
        finished_display = self.selenium.find_element_by_id('edit_task_finished')
        self.assertEqual(
            finished_display.get_attribute('innerHTML'),
            '1')
        name_input = self.selenium.find_element_by_id('edit_task_name')
        name_input.clear()
        name_input.send_keys('Edited Task')
        duration_input = self.selenium.find_element_by_id('edit_task_duration')
        duration_input.clear()
        duration_input.send_keys('42')
        self.selenium.find_element_by_xpath('//input[@value="Update Task"]').click()

        task.refresh_from_db()
        self.assertEqual(
            task.name,
            'Edited Task')
        self.assertEqual(
            task.duration,
            Decimal(42))

    def test_schedule_task_for_today(self):
        self.assertEqual(TaskExecution.objects.count(), 0)

        # create dummy task
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=5)

        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_class_name('task-schedule').click()
        name_display = self.selenium.find_element_by_id('schedule_data_name')
        self.assertEqual(
            name_display.get_attribute('innerHTML'),
            'Testtask')
        unscheduled_display = self.selenium.find_element_by_id('schedule_data_unscheduled_duration')
        self.assertEqual(
            unscheduled_display.get_attribute('innerHTML'),
            '5')
        duration_input = self.selenium.find_element_by_id('schedule_duration')
        duration_input.clear()
        duration_input.send_keys('1')
        self.selenium.find_element_by_xpath('//input[@value="Schedule"]').click()

        self.assertEqual(task.executions.count(), 1)
        execution = task.executions.first()
        self.assertEqual(execution.day, date.today())
        self.assertEqual(execution.duration, Decimal(1))
        self.assertFalse(execution.finished)

    def test_schedule_task_for_tomorrow(self):
        self.assertEqual(TaskExecution.objects.count(), 0)

        # create dummy task
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=5)

        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_class_name('task-schedule').click()
        name_display = self.selenium.find_element_by_id('schedule_data_name')
        self.assertEqual(
            name_display.get_attribute('innerHTML'),
            'Testtask')
        unscheduled_display = self.selenium.find_element_by_id('schedule_data_unscheduled_duration')
        self.assertEqual(
            unscheduled_display.get_attribute('innerHTML'),
            '5')
        duration_input = self.selenium.find_element_by_id('schedule_duration')
        duration_input.clear()
        duration_input.send_keys('1')
        Select(self.selenium.find_element_by_id('schedule_for')).select_by_visible_text(
            'Tomorrow')
        self.selenium.find_element_by_xpath('//input[@value="Schedule"]').click()

        self.assertEqual(task.executions.count(), 1)
        execution = task.executions.first()
        self.assertEqual(execution.day, date.today() + timedelta(days=1))
        self.assertEqual(execution.duration, Decimal(1))
        self.assertFalse(execution.finished)

    def test_schedule_task_for_next_free_capacity(self):
        self.assertEqual(TaskExecution.objects.count(), 0)

        # create dummy task
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=5)
        other_task = Task.objects.create(
            user=self.user,
            name='Placeholder Testtask',
            duration=30)
        # create task executions to fill current and next 2 days
        TaskExecution.objects.bulk_create([
            TaskExecution(
                task=other_task, duration=10, day=date.today(), day_order=0),
            TaskExecution(
                task=other_task, duration=10, day=date.today() + timedelta(days=1), day_order=0),
            TaskExecution(
                task=other_task, duration=10, day=date.today() + timedelta(days=2), day_order=0)])

        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_class_name('task-schedule').click()
        name_display = self.selenium.find_element_by_id('schedule_data_name')
        self.assertEqual(
            name_display.get_attribute('innerHTML'),
            'Testtask')
        unscheduled_display = self.selenium.find_element_by_id('schedule_data_unscheduled_duration')
        self.assertEqual(
            unscheduled_display.get_attribute('innerHTML'),
            '5')
        duration_input = self.selenium.find_element_by_id('schedule_duration')
        duration_input.clear()
        duration_input.send_keys('1')
        Select(self.selenium.find_element_by_id('schedule_for')).select_by_visible_text(
            'Next Free Capacity')
        self.selenium.find_element_by_xpath('//input[@value="Schedule"]').click()

        self.assertEqual(task.executions.count(), 1)
        execution = task.executions.first()
        self.assertEqual(execution.day, date.today() + timedelta(days=3))
        self.assertEqual(execution.duration, Decimal(1))
        self.assertFalse(execution.finished)

    def test_schedule_task_for_another_time(self):
        self.assertEqual(TaskExecution.objects.count(), 0)

        # create dummy task
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=5)
        other_task = Task.objects.create(
            user=self.user,
            name='Placeholder Testtask',
            duration=30)
        # create task executions to fill current and next 2 days
        TaskExecution.objects.bulk_create([
            TaskExecution(
                task=other_task, duration=10, day=date.today(), day_order=0),
            TaskExecution(
                task=other_task, duration=10, day=date.today() + timedelta(days=1), day_order=0),
            TaskExecution(
                task=other_task, duration=10, day=date.today() + timedelta(days=2), day_order=0)])

        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_class_name('task-schedule').click()
        name_display = self.selenium.find_element_by_id('schedule_data_name')
        self.assertEqual(
            name_display.get_attribute('innerHTML'),
            'Testtask')
        unscheduled_display = self.selenium.find_element_by_id('schedule_data_unscheduled_duration')
        self.assertEqual(
            unscheduled_display.get_attribute('innerHTML'),
            '5')
        duration_input = self.selenium.find_element_by_id('schedule_duration')
        duration_input.clear()
        duration_input.send_keys('1')
        Select(self.selenium.find_element_by_id('schedule_for')).select_by_visible_text(
            'Another Time')
        date_input = self.selenium.find_element_by_id('schedule_for_date')
        date_input.clear()
        date_input.send_keys('2017-01-02')
        self.selenium.find_element_by_xpath('//input[@value="Schedule"]').click()

        self.assertEqual(task.executions.count(), 1)
        execution = task.executions.first()
        self.assertEqual(execution.day, date(2017, 1, 2))
        self.assertEqual(execution.duration, Decimal(1))
        self.assertFalse(execution.finished)

    def test_schedule_task_invalid_duration(self):
        self.assertEqual(TaskExecution.objects.count(), 0)

        # create dummy task
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=5)

        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_class_name('task-schedule').click()
        name_display = self.selenium.find_element_by_id('schedule_data_name')
        self.assertEqual(
            name_display.get_attribute('innerHTML'),
            'Testtask')
        unscheduled_display = self.selenium.find_element_by_id('schedule_data_unscheduled_duration')
        self.assertEqual(
            unscheduled_display.get_attribute('innerHTML'),
            '5')
        duration_input = self.selenium.find_element_by_id('schedule_duration')
        duration_input.clear()
        duration_input.send_keys('-1')
        self.selenium.find_element_by_xpath('//input[@value="Schedule"]').click()

        self.assertEqual(task.executions.count(), 0)

    def test_task_execution_increase_time(self):
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=5)
        execution = TaskExecution.objects.create(
            day=date.today(),
            task=task,
            duration=2,
            day_order=0)

        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_css_selector('[data-tooltip="Takes 30 more minutes"]').click()

        execution.refresh_from_db()
        self.assertEqual(
            execution.duration,
            Decimal('2.5'))

    def test_task_execution_decrease_time(self):
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=5)
        execution = TaskExecution.objects.create(
            day=date.today(),
            task=task,
            duration=2,
            day_order=0)

        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_css_selector('[data-tooltip="Takes 30 less minutes"]').click()

        execution.refresh_from_db()
        self.assertEqual(
            execution.duration,
            Decimal('1.5'))

    def test_task_execution_finish(self):
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=5)
        execution = TaskExecution.objects.create(
            day=date.today(),
            task=task,
            duration=2,
            day_order=0)

        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_css_selector('[data-tooltip="Done"]').click()

        execution.refresh_from_db()
        self.assertTrue(execution.finished)

    def test_task_execution_undo(self):
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=5)
        execution = TaskExecution.objects.create(
            day=date.today(),
            task=task,
            duration=2,
            day_order=0,
            finished=True)

        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_css_selector('[data-tooltip="Not done"]').click()

        execution.refresh_from_db()
        self.assertFalse(execution.finished)

    def test_task_execution_delete(self):
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=5)
        execution = TaskExecution.objects.create(
            day=date.today(),
            task=task,
            duration=2,
            day_order=0,
            finished=True)

        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_css_selector('[data-tooltip="No time needed on this day"]').click()
        alert = self.selenium.switch_to_alert()
        alert.accept()
        self.selenium.get(self.live_server_url)

        self.assertRaises(ObjectDoesNotExist, execution.refresh_from_db)
        task.refresh_from_db()
        self.assertEqual(
            task.duration,
            Decimal(3))

    def test_task_execution_postpone(self):
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=5)
        execution = TaskExecution.objects.create(
            day=date.today(),
            task=task,
            duration=2,
            day_order=0,
            finished=True)

        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_css_selector('[data-tooltip="Postpone to another day"]').click()

        self.assertRaises(ObjectDoesNotExist, execution.refresh_from_db)
        task.refresh_from_db()
        self.assertEqual(
            task.duration,
            Decimal(5))

    def test_task_execution_up(self):
        task1 = Task.objects.create(
            user=self.user,
            name='Task 1',
            duration=5)
        execution1 = TaskExecution.objects.create(
            day=date.today(),
            task=task1,
            duration=2,
            day_order=0)
        task2 = Task.objects.create(
            user=self.user,
            name='Task 2',
            duration=5)
        execution2 = TaskExecution.objects.create(
            day=date.today(),
            task=task2,
            duration=1,
            day_order=1)

        self.selenium.get(self.live_server_url)
        self.selenium.find_elements_by_css_selector('[data-tooltip="Needs time earlier"]')[1].click()

        execution1.refresh_from_db()
        execution2.refresh_from_db()
        self.assertEqual(
            execution1.day_order,
            1)
        self.assertEqual(
            execution2.day_order,
            0)

    def test_task_execution_down(self):
        task1 = Task.objects.create(
            user=self.user,
            name='Task 1',
            duration=5)
        execution1 = TaskExecution.objects.create(
            day=date.today(),
            task=task1,
            duration=2,
            day_order=0)
        task2 = Task.objects.create(
            user=self.user,
            name='Task 2',
            duration=5)
        execution2 = TaskExecution.objects.create(
            day=date.today(),
            task=task2,
            duration=1,
            day_order=1)

        self.selenium.get(self.live_server_url)
        self.selenium.find_elements_by_css_selector('[data-tooltip="Needs time later"]')[0].click()

        execution1.refresh_from_db()
        execution2.refresh_from_db()
        self.assertEqual(
            execution1.day_order,
            1)
        self.assertEqual(
            execution2.day_order,
            0)

    def test_missed_task_execution_finish(self):
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=5)
        execution = TaskExecution.objects.create(
            day=date.today() - timedelta(days=4),
            task=task,
            duration=2,
            day_order=0)

        self.selenium.get(self.live_server_url)

        self.assertIn(
            'There are unfinished scheduled tasks for past days!',
            self.selenium.page_source)

        self.selenium.find_element_by_css_selector('[data-tooltip="Done"]').click()

        execution.refresh_from_db()
        self.assertTrue(execution.finished)

    def test_missed_task_execution_postpone(self):
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=5)
        execution = TaskExecution.objects.create(
            day=date.today() - timedelta(days=4),
            task=task,
            duration=2,
            day_order=0)

        self.selenium.get(self.live_server_url)

        self.assertIn(
            'There are unfinished scheduled tasks for past days!',
            self.selenium.page_source)

        self.selenium.find_element_by_css_selector('[data-tooltip="Postpone to another day"]').click()

        self.assertRaises(ObjectDoesNotExist, execution.refresh_from_db)

# TODO: missed task executions

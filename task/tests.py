from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from freezegun import freeze_time
from selenium.webdriver.support.ui import Select

from base.selenium_test import AuthenticatedSeleniumTest
from task.templatetags.task import more_natural_day
from .day import Day
from .models import Task, TaskExecution


class DayTest(TestCase):
    def setUp(self):
        self.user1 = get_user_model().objects.create(
            username='johndoe',
            email='a',
            workhours_weekday=Decimal(10),
            workhours_weekend=Decimal(5))
        self.user2 = get_user_model().objects.create(
            username='foobar',
            email='b')

        self.weekenddate1 = date(2017, 11, 5)
        self.weekdaydate1 = date(2017, 11, 6)
        self.weekdaydate2 = date(2017, 11, 7)
        self.weekdaydate3 = date(2017, 11, 8)

        self.todaydate = date.today()

        self.futuredate1 = self.todaydate + timedelta(days=5)

    def test_eq_for_different_days(self):
        self.assertEqual(
            Day(self.user1, self.weekenddate1),
            Day(self.user1, self.weekenddate1))
        self.assertNotEqual(
            Day(self.user1, self.weekenddate1),
            Day(self.user1, self.weekdaydate1))

    def test_eq_for_different_users(self):
        self.assertNotEqual(
            Day(self.user1, self.weekenddate1),
            Day(self.user2, self.weekenddate1))

    def test_eq_for_different_days_and_users(self):
        self.assertNotEqual(
            Day(self.user1, self.weekdaydate1),
            Day(self.user2, self.weekenddate1))

    def test_hash_for_different_days(self):
        self.assertEqual(
            hash(Day(self.user1, self.weekenddate1)),
            hash(Day(self.user1, self.weekenddate1)))
        self.assertNotEqual(
            hash(Day(self.user1, self.weekenddate1)),
            hash(Day(self.user1, self.weekdaydate1)))

    def test_hash_for_different_users(self):
        self.assertNotEqual(
            hash(Day(self.user1, self.weekenddate1)),
            hash(Day(self.user2, self.weekenddate1)))

    def test_hash_for_different_days_and_users(self):
        self.assertNotEqual(
            hash(Day(self.user1, self.weekdaydate1)),
            hash(Day(self.user2, self.weekenddate1)))

    def test_is_weekday(self):
        self.assertTrue(
            Day(self.user1, self.weekdaydate1).is_weekday())
        self.assertFalse(
            Day(self.user1, self.weekenddate1).is_weekday())

    def test_in_past(self):
        self.assertTrue(
            Day(self.user1, self.weekdaydate1).in_past())
        self.assertFalse(
            Day(self.user1, self.todaydate).in_past())
        self.assertFalse(
            Day(self.user1, self.futuredate1).in_past())

    def test_is_today(self):
        self.assertTrue(
            Day(self.user1, self.todaydate).is_today())
        self.assertFalse(
            Day(self.user1, self.weekdaydate1).is_today())
        self.assertFalse(
            Day(self.user1, self.futuredate1).is_today())

    def test_scheduled_duration(self):
        day = Day(self.user1, self.weekdaydate1)
        self.assertEqual(
            day.scheduled_duration,
            0)
        day.executions.append(
            TaskExecution(duration=3))
        self.assertEqual(
            day.scheduled_duration,
            3)
        day.executions.append(
            TaskExecution(duration=2))
        self.assertEqual(
            day.scheduled_duration,
            5)

    def test_available_duration_weekday(self):
        day = Day(self.user1, self.weekdaydate1)
        self.assertEqual(
            day.available_duration,
            10)
        day.executions.append(
            TaskExecution(duration=3))
        self.assertEqual(
            day.available_duration,
            7)
        day.executions.append(
            TaskExecution(duration=10))
        self.assertEqual(
            day.available_duration,
            -3)
        day.executions.append(
            TaskExecution(duration=10))
        self.assertEqual(
            day.available_duration,
            -13)

    def test_available_duration_weekend(self):
        day = Day(self.user1, self.weekenddate1)
        self.assertEqual(
            day.available_duration,
            5)
        day.executions.append(
            TaskExecution(duration=3))
        self.assertEqual(
            day.available_duration,
            2)
        day.executions.append(
            TaskExecution(duration=10))
        self.assertEqual(
            day.available_duration,
            -8)
        day.executions.append(
            TaskExecution(duration=10))
        self.assertEqual(
            day.available_duration,
            -18)

    def test_max_duration_weekday(self):
        day = Day(self.user1, self.weekdaydate1)
        self.assertEqual(
            day.max_duration,
            10)

    def test_max_duration_weekend(self):
        day = Day(self.user1, self.weekenddate1)
        self.assertEqual(
            day.max_duration,
            5)

    def test_duration_types(self):
        day = Day(self.user1, self.weekenddate1)
        self.assertIsInstance(
            day.scheduled_duration,
            Decimal)
        self.assertIsInstance(
            day.available_duration,
            Decimal)
        self.assertIsInstance(
            day.max_duration,
            Decimal)
        day.executions.append(
            TaskExecution(duration=10))
        self.assertIsInstance(
            day.scheduled_duration,
            Decimal)
        self.assertIsInstance(
            day.available_duration,
            Decimal)
        self.assertIsInstance(
            day.max_duration,
            Decimal)
        day.executions.append(
            TaskExecution(duration=7))
        self.assertIsInstance(
            day.scheduled_duration,
            Decimal)
        self.assertIsInstance(
            day.available_duration,
            Decimal)
        self.assertIsInstance(
            day.max_duration,
            Decimal)

    def test_finished_duration(self):
        day = Day(self.user1, self.weekenddate1)
        self.assertEqual(
            day.finished_duration,
            0)
        execution1 = TaskExecution(duration=2)
        day.executions.append(execution1)
        self.assertEqual(
            day.finished_duration,
            0)
        execution1.finished = True
        self.assertEqual(
            day.finished_duration,
            2)
        execution2 = TaskExecution(duration=4)
        day.executions.append(execution2)
        self.assertEqual(
            day.finished_duration,
            2)
        execution2.finished = True
        self.assertEqual(
            day.finished_duration,
            6)

    def test_remaining_duration(self):
        day = Day(self.user1, self.weekenddate1)
        self.assertEqual(
            day.remaining_duration,
            0)
        execution1 = TaskExecution(duration=2)
        day.executions.append(execution1)
        self.assertEqual(
            day.remaining_duration,
            2)
        execution2 = TaskExecution(duration=1)
        day.executions.append(execution2)
        self.assertEqual(
            day.remaining_duration,
            3)
        execution1.finished = True
        self.assertEqual(
            day.remaining_duration,
            1)
        execution2.finished = True
        self.assertEqual(
            day.remaining_duration,
            0)
        execution1.finished = False
        self.assertEqual(
            day.remaining_duration,
            2)


class TemplateTagsTest(TestCase):
    @freeze_time('2017-11-16')
    def test_more_natural_day(self):
        base_date = date(2017, 11, 16)

        day = base_date - timedelta(days=3)
        self.assertEqual(
            more_natural_day(day),
            'Nov. 13, 2017'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day),
            'Nov. 14, 2017'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day),
            'yesterday'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day),
            'today'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day),
            'tomorrow'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day),
            'Saturday'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day),
            'Sunday'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day),
            'Monday'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day),
            'Tuesday'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day),
            'Wednesday'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day),
            'Nov. 23, 2017'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day),
            'Nov. 24, 2017'
        )


class TaskTest(TestCase):
    def setUp(self):
        self.user1 = get_user_model().objects.create(
            username='johndoe',
            email='a',
            workhours_weekday=Decimal(10),
            workhours_weekend=Decimal(5),
            default_schedule_duration=Decimal(1),
            default_schedule_full_duration_max=Decimal(3),
        )
        self.user2 = get_user_model().objects.create(
            username='foobar',
            email='b',
            default_schedule_duration=Decimal(2),
            default_schedule_full_duration_max=Decimal(5),
        )

        self.weekdaydate1 = date(2017, 11, 6)

    def test_finished_duration(self):
        task1 = Task.objects.create(user=self.user1, duration=42)
        self.assertEqual(
            task1.finished_duration,
            0)
        exec1 = TaskExecution.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=4,
            finished=False)
        self.assertEqual(
            task1.finished_duration,
            0)
        exec1.finished = True
        exec1.save()
        self.assertEqual(
            task1.finished_duration,
            4)
        exec2 = TaskExecution.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=2,
            finished=False)
        self.assertEqual(
            task1.finished_duration,
            4)
        exec2.finished = True
        exec2.save()
        self.assertEqual(
            task1.finished_duration,
            6)
        exec1.finished = False
        exec1.save()
        self.assertEqual(
            task1.finished_duration,
            2)

    def test_scheduled_duration(self):
        task1 = Task.objects.create(user=self.user1, duration=42)
        self.assertEqual(
            task1.scheduled_duration,
            0)
        exec1 = TaskExecution.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=4,
            finished=False)
        self.assertEqual(
            task1.scheduled_duration,
            4)
        exec1.finished = True
        exec1.save()
        self.assertEqual(
            task1.scheduled_duration,
            4)
        exec2 = TaskExecution.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=2,
            finished=False)
        self.assertEqual(
            task1.scheduled_duration,
            6)
        exec2.finished = True
        exec2.save()
        self.assertEqual(
            task1.scheduled_duration,
            6)
        exec1.finished = False
        exec1.save()
        self.assertEqual(
            task1.scheduled_duration,
            6)

    def test_unscheduled_duration(self):
        task1 = Task.objects.create(user=self.user1, duration=42)
        self.assertEqual(
            task1.unscheduled_duration,
            42)
        exec1 = TaskExecution.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=4,
            finished=False)
        self.assertEqual(
            task1.unscheduled_duration,
            38)
        exec1.finished = True
        exec1.save()
        self.assertEqual(
            task1.unscheduled_duration,
            38)
        exec2 = TaskExecution.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=2,
            finished=False)
        self.assertEqual(
            task1.unscheduled_duration,
            36)
        exec2.finished = True
        exec2.save()
        self.assertEqual(
            task1.unscheduled_duration,
            36)
        exec1.finished = False
        exec1.save()
        self.assertEqual(
            task1.unscheduled_duration,
            36)

    def test_unscheduled_tasks(self):
        self.assertEqual(
            set(Task.unscheduled_tasks(self.user1)),
            set())
        self.assertEqual(
            set(Task.unscheduled_tasks(self.user2)),
            set())
        task1 = Task.objects.create(user=self.user1, duration=2)
        self.assertEqual(
            set(Task.unscheduled_tasks(self.user1)),
            {task1})
        self.assertEqual(
            set(Task.unscheduled_tasks(self.user2)),
            set())
        exec1 = TaskExecution.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=1,
            finished=False)
        self.assertEqual(
            set(Task.unscheduled_tasks(self.user1)),
            {task1})
        self.assertEqual(
            set(Task.unscheduled_tasks(self.user2)),
            set())
        exec2 = TaskExecution.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=1,
            finished=False)
        self.assertEqual(
            set(Task.unscheduled_tasks(self.user1)),
            set())
        self.assertEqual(
            set(Task.unscheduled_tasks(self.user2)),
            set())
        exec2.finished = True
        exec2.save()
        self.assertEqual(
            set(Task.unscheduled_tasks(self.user1)),
            set())
        self.assertEqual(
            set(Task.unscheduled_tasks(self.user2)),
            set())
        exec1.finished = True
        exec1.save()
        self.assertEqual(
            set(Task.unscheduled_tasks(self.user1)),
            set())
        self.assertEqual(
            set(Task.unscheduled_tasks(self.user2)),
            set())

    def test_default_schedule_duration(self):
        task = Task.objects.create(
            name='testtask',
            user=self.user1,
            duration=Decimal(42),
        )
        exec = TaskExecution.objects.create(
            task=task,
            day=self.weekdaydate1,
            day_order=1,
            duration=0,
        )
        exec.duration = Decimal(42) - Decimal(42)
        exec.save()
        self.assertEqual(task.default_schedule_duration, Decimal(1))
        exec.duration = Decimal(42) - Decimal(13)
        exec.save()
        self.assertEqual(task.default_schedule_duration, Decimal(1))
        exec.duration = Decimal(42) - Decimal(3)
        exec.save()
        self.assertEqual(task.default_schedule_duration, Decimal(3))
        exec.duration = Decimal(42) - Decimal('2.5')
        exec.save()
        self.assertEqual(task.default_schedule_duration, Decimal('2.5'))
        exec.duration = Decimal(42) - Decimal('1.5')
        exec.save()
        self.assertEqual(task.default_schedule_duration, Decimal('1.5'))
        exec.duration = Decimal(42) - Decimal('0.5')
        exec.save()
        self.assertEqual(task.default_schedule_duration, Decimal('0.5'))
        exec.duration = Decimal(42) - Decimal(0)
        exec.save()
        self.assertEqual(task.default_schedule_duration, Decimal(0))

        task.user = self.user2
        exec.duration = Decimal(42) - Decimal(42)
        exec.save()
        self.assertEqual(task.default_schedule_duration, Decimal(2))
        exec.duration = Decimal(42) - Decimal(13)
        exec.save()
        self.assertEqual(task.default_schedule_duration, Decimal(2))
        exec.duration = Decimal(42) - Decimal(5)
        exec.save()
        self.assertEqual(task.default_schedule_duration, Decimal(5))
        exec.duration = Decimal(42) - Decimal(3)
        exec.save()
        self.assertEqual(task.default_schedule_duration, Decimal(3))
        exec.duration = Decimal(42) - Decimal('2.5')
        exec.save()
        self.assertEqual(task.default_schedule_duration, Decimal('2.5'))
        exec.duration = Decimal(42) - Decimal('1.5')
        exec.save()
        self.assertEqual(task.default_schedule_duration, Decimal('1.5'))
        exec.duration = Decimal(42) - Decimal('0.5')
        exec.save()
        self.assertEqual(task.default_schedule_duration, Decimal('0.5'))
        exec.duration = Decimal(42) - Decimal(0)
        exec.save()
        self.assertEqual(task.default_schedule_duration, Decimal(0))

    def test_free_capacity(self):
        self.assertEqual(
            Task.free_capacity(self.user1, self.weekdaydate1),
            Decimal(10))
        task1 = Task.objects.create(user=self.user1, duration=2)
        self.assertEqual(
            Task.free_capacity(self.user1, self.weekdaydate1),
            Decimal(10))
        exec1 = TaskExecution.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=1,
            finished=False)
        self.assertEqual(
            Task.free_capacity(self.user1, self.weekdaydate1),
            Decimal(9))
        exec1.finished = True
        exec1.save()
        self.assertEqual(
            Task.free_capacity(self.user1, self.weekdaydate1),
            Decimal(9))

    def test_duration_types(self):
        task1 = Task.objects.create(user=self.user1, duration=42)
        self.assertIsInstance(
            task1.finished_duration,
            Decimal)
        self.assertIsInstance(
            task1.scheduled_duration,
            Decimal)
        self.assertIsInstance(
            task1.unscheduled_duration,
            Decimal)
        TaskExecution.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=4,
            finished=False)
        self.assertIsInstance(
            task1.finished_duration,
            Decimal)
        self.assertIsInstance(
            task1.scheduled_duration,
            Decimal)
        self.assertIsInstance(
            task1.unscheduled_duration,
            Decimal)


class TaskExecutionTest(TestCase):
    def setUp(self):
        self.user1 = get_user_model().objects.create(
            username='johndoe',
            email='a',
            workhours_weekday=Decimal(10),
            workhours_weekend=Decimal(5),
            default_schedule_duration=Decimal(1),
            default_schedule_full_duration_max=Decimal(3),
        )
        self.user2 = get_user_model().objects.create(
            username='foobar',
            email='b',
            default_schedule_duration=Decimal(2),
            default_schedule_full_duration_max=Decimal(5),
        )
        self.weekdaydate1 = date(2017, 11, 6)

    @freeze_time('2017-11-16')
    def test_missed_task_executions(self):
        self.assertListEqual(
            list(TaskExecution.missed_task_executions(self.user1)),
            [])
        self.assertListEqual(
            list(TaskExecution.missed_task_executions(self.user2)),
            [])

        task1 = Task.objects.create(
            user=self.user1,
            duration=Decimal(42))

        self.assertListEqual(
            list(TaskExecution.missed_task_executions(self.user1)),
            [])
        self.assertListEqual(
            list(TaskExecution.missed_task_executions(self.user2)),
            [])

        TaskExecution.objects.create(
            task=task1,
            duration=1,
            day=date(2018, 1, 1),
            day_order=1,
        )

        self.assertListEqual(
            list(TaskExecution.missed_task_executions(self.user1)),
            [])
        self.assertListEqual(
            list(TaskExecution.missed_task_executions(self.user2)),
            [])

        exec2 = TaskExecution.objects.create(
            task=task1,
            duration=1,
            day=date(2017, 1, 1),
            day_order=1,
        )

        self.assertListEqual(
            list(TaskExecution.missed_task_executions(self.user1)),
            [exec2])
        self.assertListEqual(
            list(TaskExecution.missed_task_executions(self.user2)),
            [])

        exec3 = TaskExecution.objects.create(
            task=task1,
            duration=1,
            day=date(2015, 5, 1),
            day_order=1,
        )
        self.assertListEqual(
            list(TaskExecution.missed_task_executions(self.user1)),
            [exec3, exec2])
        self.assertListEqual(
            list(TaskExecution.missed_task_executions(self.user2)),
            [])

        exec3.finished = True
        exec3.save(update_fields=('finished',))
        self.assertListEqual(
            list(TaskExecution.missed_task_executions(self.user1)),
            [exec2])
        self.assertListEqual(
            list(TaskExecution.missed_task_executions(self.user2)),
            [])
        exec2.finished = True
        exec2.save(update_fields=('finished',))
        self.assertListEqual(
            list(TaskExecution.missed_task_executions(self.user1)),
            [])
        self.assertListEqual(
            list(TaskExecution.missed_task_executions(self.user2)),
            [])


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

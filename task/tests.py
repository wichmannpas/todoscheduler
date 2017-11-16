from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from task.templatetags.task import more_natural_day
from .day import Day
from .models import TaskExecution


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
    def test_more_natural_day(self):
        base_date = date(2017, 11, 16)

        day = base_date - timedelta(days=3)
        self.assertEqual(
            more_natural_day(day, base_date),
            'Nov. 13, 2017'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day, base_date),
            'Nov. 14, 2017'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day, base_date),
            'yesterday'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day, base_date),
            'today'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day, base_date),
            'tomorrow'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day, base_date),
            'Saturday'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day, base_date),
            'Sunday'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day, base_date),
            'Monday'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day, base_date),
            'Tuesday'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day, base_date),
            'Wednesday'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day, base_date),
            'Nov. 23, 2017'
        )
        day += timedelta(days=1)
        self.assertEqual(
            more_natural_day(day, base_date),
            'Nov. 24, 2017'
        )

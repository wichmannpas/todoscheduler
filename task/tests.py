from datetime import date, timedelta
from decimal import Decimal
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from freezegun import freeze_time
from rest_framework import status

from base.tests import AuthenticatedApiTest
from .models import Task, TaskExecution


class TaskViewTest(AuthenticatedApiTest):
    def test_create_task(self):
        """
        Test the creation of a new task.
        """
        resp = self.client.post('/task/task/', {
            'name': 'Testtask',
            'duration': '2.5',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)

        self.assertEqual(
            Task.objects.count(),
            1)

        task = Task.objects.first()
        self.assertEqual(
            task.user,
            self.user)
        self.assertEqual(
            task.name,
            'Testtask')
        self.assertEqual(
            task.duration,
            Decimal('2.5'))

    def test_create_task_invalid_duration(self):
        """
        Test the creation of a new task with an invalid duration.
        """
        resp = self.client.post('/task/task/', {
            'name': 'Testtask',
            'duration': '-2',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            Task.objects.count(),
            0)

    def test_update_task_duration_less_than_scheduled(self):
        """
        Test setting the duration of a task that is less than the
        scheduled duration.
        """
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=Decimal(2))
        TaskExecution.objects.create(
            task=task,
            day=date(2000, 1, 2),
            day_order=0,
            duration=Decimal(1))
        resp = self.client.patch('/task/task/{}/'.format(task.pk), {
            'duration': '0.5',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)

        task.refresh_from_db()
        self.assertEqual(
            task.duration,
            Decimal(2))

    def test_update_task_duration_to_scheduled(self):
        """
        Test setting the duration of a task to exactly the scheduled duration.
        """
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=Decimal(2))
        TaskExecution.objects.create(
            task=task,
            day=date(2000, 1, 2),
            day_order=0,
            duration=Decimal('0.5'))
        resp = self.client.patch('/task/task/{}/'.format(task.pk), {
            'duration': '0.5',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)

        task.refresh_from_db()
        self.assertEqual(
            task.duration,
            Decimal('0.5'))

    def test_get_task(self):
        """
        Test the retrieval of an existing task.
        """
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=Decimal(2))
        resp = self.client.get('/task/task/{}/'.format(task.id))
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            resp.data['name'],
            'Testtask')
        self.assertEqual(
            resp.data['duration'],
            '2.00')

    def test_no_getting_of_foreign_task(self):
        """
        Test the retrieval of an existing task of a different user.
        This is expected to be not found.
        """
        foreign_user = get_user_model().objects.create(
            username='foreign')
        task = Task.objects.create(
            user=foreign_user,
            name='Testtask',
            duration=Decimal(2))
        resp = self.client.get('/task/task/{}/'.format(task.id))
        self.assertEqual(
            resp.status_code,
            status.HTTP_404_NOT_FOUND)

    def test_delete_task(self):
        """
        Test the deletion of an existing task.
        """
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=Decimal(2))
        resp = self.client.delete('/task/task/{}/'.format(task.id))
        self.assertEqual(
            resp.status_code,
            status.HTTP_204_NO_CONTENT)
        self.assertRaises(
            ObjectDoesNotExist,
            task.refresh_from_db)

    def test_update_task(self):
        """
        Test the update of an existing task using both
        POST and PATCH.
        """
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=Decimal(2))
        resp = self.client.patch('/task/task/{}/'.format(task.id), {
            'name': 'Renamed testtask',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(
            task.name,
            'Renamed testtask')

        resp = self.client.put('/task/task/{}/'.format(task.id), {
            'name': 'Renamed testtask',
            'duration': '42',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(
            task.name,
            'Renamed testtask')
        self.assertEqual(
            task.duration,
            Decimal(42))

    def test_list_all_tasks(self):
        """
        Test the listing of all own tasks.
        """
        Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=Decimal(2))
        Task.objects.create(
            user=self.user,
            name='Second Testtask',
            duration=Decimal(3))

        resp = self.client.get('/task/task/')
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            2)

    @freeze_time('2001-02-03')
    def test_list_all_tasks_ordering(self):
        """
        Test that the ordering of the task listing is
        correct.
        """
        Task.objects.create(
            user=self.user,
            name='A Testtask',
            duration=Decimal(2))
        Task.objects.create(
            user=self.user,
            name='B Testtask',
            duration=Decimal(3))
        Task.objects.create(
            user=self.user,
            name='0 Testtask',
            duration=Decimal(3),
            start=date(2001, 2, 10))
        Task.objects.create(
            user=self.user,
            name='1 Testtask',
            duration=Decimal(3),
            start=date(2001, 2, 9))

        resp = self.client.get('/task/task/')
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertListEqual(
            [
                item['name']
                for item in resp.data
            ],
            [
                'A Testtask',
                'B Testtask',
                '1 Testtask',
                '0 Testtask',
            ])

    def test_list_incomplete_tasks(self):
        """
        Test the filtering for incomplete tasks.
        """
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=Decimal(2))
        TaskExecution.objects.create(
            task=task,
            day=date(2010, 5, 14),
            duration=Decimal(2))

        Task.objects.create(
            user=self.user,
            name='Second Testtask',
            duration=Decimal(3))

        foreign_user = get_user_model().objects.create(
            username='foreign')
        Task.objects.create(
            user=foreign_user,
            name='Foreign Testtask',
            duration=Decimal(3))

        resp = self.client.get('/task/task/')
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            2)

        resp = self.client.get('/task/task/?incomplete')
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            1)

    def test_no_listing_of_foreign_tasks(self):
        """
        Test that tasks of other users are not listed.
        """
        other_user = get_user_model().objects.create(
            username='other',
            workhours_weekday=Decimal(10),
            workhours_weekend=Decimal(5),
            default_schedule_duration=Decimal(1),
            default_schedule_full_duration_max=Decimal(3),
        )
        Task.objects.create(
            user=other_user,
            name='foreign task',
            duration=2)

        Task.objects.create(
            user=self.user,
            name='own task',
            duration=2)

        resp = self.client.get('/task/task/')
        self.assertEqual(
            len(resp.data),
            1)
        self.assertEqual(
            resp.data[0]['name'],
            'own task')

        resp = self.client.get('/task/task/?incomplete')
        self.assertEqual(
            len(resp.data),
            1)
        self.assertEqual(
            resp.data[0]['name'],
            'own task')


class TaskExecutionViewTest(AuthenticatedApiTest):
    def setUp(self):
        super().setUp()

        self.day = date(2001, 2, 3)
        self.day2 = date(2001, 2, 4)

        self.task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=Decimal(2))

    def test_finish_task_execution(self):
        """Test finishing a task execution."""
        task_execution = TaskExecution.objects.create(
            task=self.task,
            day=self.day,
            day_order=0,
            duration=Decimal(1))

        self.assertEqual(
            task_execution.finished,
            False)

        resp = self.client.patch('/task/taskexecution/{}/'.format(task_execution.pk), {
            'finished': True,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)

        task_execution.refresh_from_db()
        self.assertEqual(
            task_execution.finished,
            True)

    def test_unfinish_task_execution(self):
        """Test unfinishing a task execution."""
        task_execution = TaskExecution.objects.create(
            task=self.task,
            day=self.day,
            day_order=0,
            duration=Decimal(1),
            finished=True)

        self.assertEqual(
            task_execution.finished,
            True)

        resp = self.client.patch('/task/taskexecution/{}/'.format(task_execution.pk), {
            'finished': False,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)

        task_execution.refresh_from_db()
        self.assertEqual(
            task_execution.finished,
            False)

    def test_delete_task_execution(self):
        """Test the deletion of a task execution without postponing."""
        task_execution = TaskExecution.objects.create(
            task=self.task,
            day=self.day,
            day_order=0,
            duration=Decimal(1))

        resp = self.client.delete('/task/taskexecution/{}/?postpone=0'.format(task_execution.pk))
        self.assertEqual(
            resp.status_code,
            status.HTTP_204_NO_CONTENT)

        self.assertRaises(
            ObjectDoesNotExist,
            task_execution.refresh_from_db)
        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            Decimal(1))

    def test_delete_task_execution_with_task(self):
        """
        Test the deletion of a task execution without postponing.

        The task should be deleted as well because the task execution
        duration matches the task duration.
        """
        task_execution = TaskExecution.objects.create(
            task=self.task,
            day=self.day,
            day_order=0,
            duration=Decimal(2))

        resp = self.client.delete('/task/taskexecution/{}/?postpone=0'.format(task_execution.pk))
        self.assertEqual(
            resp.status_code,
            status.HTTP_204_NO_CONTENT)

        self.assertRaises(
            ObjectDoesNotExist,
            task_execution.refresh_from_db)
        self.assertRaises(
            ObjectDoesNotExist,
            self.task.refresh_from_db)

    def test_postpone_task_execution(self):
        """Test the deletion of a task execution with postponing."""
        task_execution = TaskExecution.objects.create(
            task=self.task,
            day=self.day,
            day_order=0,
            duration=Decimal(1))

        resp = self.client.delete('/task/taskexecution/{}/?postpone=1'.format(task_execution.pk))
        self.assertEqual(
            resp.status_code,
            status.HTTP_204_NO_CONTENT)

        self.assertRaises(
            ObjectDoesNotExist,
            task_execution.refresh_from_db)
        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            Decimal(2))

    def test_change_duration(self):
        """
        Test changing the duration of the task execution.
        This should change the task duration as well.
        """
        task_execution = TaskExecution.objects.create(
            task=self.task,
            day=self.day,
            day_order=0,
            duration=Decimal(1),
            finished=True)

        self.assertEqual(
            task_execution.finished,
            True)

        resp = self.client.patch('/task/taskexecution/{}/'.format(task_execution.pk), {
            'duration': 4,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)

        task_execution.refresh_from_db()
        self.assertEqual(
            task_execution.duration,
            Decimal(4))
        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            Decimal(5))  # 2 + (4 - 1)

        resp = self.client.patch('/task/taskexecution/{}/'.format(task_execution.pk), {
            'duration': '0.5',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)

        task_execution.refresh_from_db()
        self.assertEqual(
            task_execution.duration,
            Decimal('0.5'))
        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            Decimal('1.5'))  # 5 + (0.5 - 4)

    def test_change_duration_invalid(self):
        """
        Test changing the duration of the task execution to an invalid value.
        """
        task_execution = TaskExecution.objects.create(
            task=self.task,
            day=self.day,
            day_order=0,
            duration=Decimal(1),
            finished=True)

        self.assertEqual(
            task_execution.finished,
            True)

        resp = self.client.patch('/task/taskexecution/{}/'.format(task_execution.pk), {
            'duration': -4,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)

        task_execution.refresh_from_db()
        self.assertEqual(
            task_execution.duration,
            Decimal(1))

    def test_exchange_task_execution(self):
        """Test exchanging a task execution with another."""
        task_execution1 = TaskExecution.objects.create(
            task=self.task,
            day=self.day,
            duration=Decimal(1),
            day_order=1
        )
        task_execution2 = TaskExecution.objects.create(
            task=self.task,
            day=self.day,
            duration=Decimal(1),
            day_order=2
        )

        resp = self.client.patch('/task/taskexecution/{}/'.format(task_execution1.pk), {
            'day_order': 2,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        task_execution1.refresh_from_db()
        self.assertEqual(
            task_execution1.day_order,
            2)
        task_execution2.refresh_from_db()
        self.assertEqual(
            task_execution2.day_order,
            1)

        resp = self.client.put('/task/taskexecution/{}/'.format(task_execution1.pk), {
            'task_id': self.task.id,
            'day': '2001-02-03',
            'duration': 1,
            'day_order': 1,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        task_execution1.refresh_from_db()
        self.assertEqual(
            task_execution1.day_order,
            1)
        task_execution2.refresh_from_db()
        self.assertEqual(
            task_execution2.day_order,
            2)

    def test_task_execution_change_day(self):
        """
        Test changing the day of a task execution. The submitted
        day order should be ignored and the execution placed at the
        end of the new day.
        """
        task_execution1 = TaskExecution.objects.create(
            task=self.task,
            day=self.day,
            duration=Decimal(1),
            day_order=1
        )
        task_execution2 = TaskExecution.objects.create(
            task=self.task,
            day=self.day2,
            duration=Decimal(1),
            day_order=1
        )

        resp = self.client.patch('/task/taskexecution/{}/'.format(task_execution1.pk), {
            'day': '2001-02-04',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        task_execution1.refresh_from_db()
        self.assertEqual(
            task_execution1.day_order,
            2)
        self.assertEqual(
            task_execution1.day,
            self.day2)
        task_execution2.refresh_from_db()
        self.assertEqual(
            task_execution2.day_order,
            1)

        # provided day order should be ignored
        resp = self.client.put('/task/taskexecution/{}/'.format(task_execution1.pk), {
            'task_id': self.task.id,
            'day': '2001-02-01',
            'duration': 1,
            'day_order': 42,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        task_execution1.refresh_from_db()
        self.assertEqual(
            task_execution1.day_order,
            1)
        self.assertEqual(
            task_execution1.day,
            date(2001, 2, 1))
        task_execution2.refresh_from_db()
        self.assertEqual(
            task_execution2.day_order,
            1)

        resp = self.client.patch('/task/taskexecution/{}/'.format(task_execution1.pk), {
            'day': '2001-02-01',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        task_execution1.refresh_from_db()
        self.assertEqual(
            task_execution1.day_order,
            1)
        self.assertEqual(
            task_execution1.day,
            date(2001, 2, 1))

    def test_explicit_creation(self):
        """
        Test the explicit creation of a new task execution.
        """
        resp = self.client.post('/task/taskexecution/', {
            'task_id': self.task.id,
            'day': '2001-02-03',
            'day_order': 0,
            'duration': 2,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_execution = TaskExecution.objects.get(
            pk=resp.data['id'])
        self.assertEqual(
            task_execution.task,
            self.task)
        self.assertEqual(
            task_execution.day,
            self.day)
        self.assertEqual(
            task_execution.day_order,
            0)
        self.assertEqual(
            task_execution.duration,
            Decimal(2))

        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            Decimal(2))

    def test_explicit_creation_task_duration_increase(self):
        """
        Test the explicit creation of a new task execution with a duration longer
        than the task duration. The task duration should be increased.
        """
        resp = self.client.post('/task/taskexecution/', {
            'task_id': self.task.id,
            'day': '2001-02-03',
            'day_order': 0,
            'duration': 5,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_execution = TaskExecution.objects.get(
            pk=resp.data['id'])
        self.assertEqual(
            task_execution.task,
            self.task)
        self.assertEqual(
            task_execution.day,
            self.day)
        self.assertEqual(
            task_execution.day_order,
            0)
        self.assertEqual(
            task_execution.duration,
            Decimal(5))

        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            Decimal(5))

    def test_explicit_creation_day_order(self):
        """
        Test that the day order is set correctly when explicitly
        creating multiple task executions without specifying a day order.
        """
        resp = self.client.post('/task/taskexecution/', {
            'task_id': self.task.id,
            'day': '2001-02-03',
            'duration': '0.5',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_execution1 = TaskExecution.objects.get(
            pk=resp.data['id'])

        resp = self.client.post('/task/taskexecution/', {
            'task_id': self.task.id,
            'day': '2001-02-04',
            'duration': '0.5',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_execution2 = TaskExecution.objects.get(
            pk=resp.data['id'])

        resp = self.client.post('/task/taskexecution/', {
            'task_id': self.task.id,
            'day': '2001-02-03',
            'duration': '0.1',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_execution3 = TaskExecution.objects.get(
            pk=resp.data['id'])

        resp = self.client.post('/task/taskexecution/', {
            'task_id': self.task.id,
            'day': '2001-02-03',
            'duration': '0.1',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_execution4 = TaskExecution.objects.get(
            pk=resp.data['id'])

        self.assertGreater(
            task_execution4.day_order,
            task_execution3.day_order,
            task_execution1.day_order)

        # both task executions were the first of their day
        self.assertEqual(
            task_execution1.day_order,
            task_execution2.day_order)

    def test_explicit_creation_too_high_duration(self):
        """
        Explicitly create a new task execution.
        Try to set the duration higher than the incomplete duration of
        the task.
        The task duration should be increased in that case.
        """
        TaskExecution.objects.create(
            task=self.task,
            day=self.day,
            duration=Decimal(1),
            finished=True)

        resp = self.client.post('/task/taskexecution/', {
            'task_id': self.task.id,
            'day': '2001-02-03',
            'duration': 5,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_execution = TaskExecution.objects.get(
            pk=resp.data['id'])
        self.assertEqual(
            task_execution.task,
            self.task)
        self.assertEqual(
            task_execution.day,
            self.day)
        self.assertEqual(
            task_execution.duration,
            Decimal(5))

        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            Decimal(6))  # 1 + (5 - 1)

    @freeze_time('2001-02-03')
    def test_schedule_for_today(self):
        """Test scheduling for current day."""
        resp = self.client.post('/task/taskexecution/', {
            'task_id': self.task.id,
            'day': 'today',
            'duration': 2,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_execution = TaskExecution.objects.get(
            pk=resp.data['id'])
        self.assertEqual(
            task_execution.task,
            self.task)
        self.assertEqual(
            task_execution.day,
            self.day)
        self.assertEqual(
            task_execution.duration,
            Decimal(2))

        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            Decimal(2))

    @freeze_time('2001-02-03')
    def test_schedule_for_tomorrow(self):
        """Test scheduling for the next day."""
        resp = self.client.post('/task/taskexecution/', {
            'task_id': self.task.id,
            'day': 'tomorrow',
            'duration': 2,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_execution = TaskExecution.objects.get(
            pk=resp.data['id'])
        self.assertEqual(
            task_execution.task,
            self.task)
        self.assertEqual(
            task_execution.day,
            self.day + timedelta(days=1))
        self.assertEqual(
            task_execution.duration,
            Decimal(2))

        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            Decimal(2))

    @freeze_time('2001-02-03')
    def test_schedule_next_free_capacity(self):
        """Test scheduling for the next free capacity."""
        task2 = Task.objects.create(
            user=self.user,
            name='Other Testtask',
            duration=Decimal(30))
        TaskExecution.objects.create(
            task=task2,
            day=self.day,  # Saturday
            duration=Decimal(5))
        TaskExecution.objects.create(
            task=task2,
            day=self.day + timedelta(days=1),  # Sunday
            duration=Decimal(5))
        TaskExecution.objects.create(
            task=task2,
            day=self.day + timedelta(days=2),  # Monday
            duration=Decimal(7))

        self.task.duration = 10
        self.task.save()

        resp = self.client.post('/task/taskexecution/', {
            'task_id': self.task.id,
            'day': 'next_free_capacity',
            'duration': 9,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_execution = TaskExecution.objects.get(
            pk=resp.data['id'])
        self.assertEqual(
            task_execution.task,
            self.task)
        self.assertEqual(
            task_execution.day,
            self.day + timedelta(days=3))  # Tuesday
        self.assertEqual(
            task_execution.duration,
            Decimal(9))

        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            Decimal(10))

    def test_task_execution_min_filter(self):
        TaskExecution.objects.create(
            task=self.task,
            duration=4,
            day=date(2018, 1, 15))
        TaskExecution.objects.create(
            task=self.task,
            duration=8,
            day=date(2018, 1, 12))
        TaskExecution.objects.create(
            task=self.task,
            duration=2,
            day=date(2018, 1, 17))

        resp = self.client.get('/task/taskexecution/')
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            3)

        resp = self.client.get('/task/taskexecution/?' + urlencode({
            'min_date': '2018-01-14',
        }))
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            2)
        self.assertSetEqual(
            {ex['day'] for ex in resp.data},
            {
                '2018-01-15',
                '2018-01-17',
            })

        resp = self.client.get('/task/taskexecution/?' + urlencode({
            'min_date': '2018-02-14',
        }))
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            0)

    def test_task_execution_max_filter(self):
        TaskExecution.objects.create(
            task=self.task,
            duration=4,
            day=date(2018, 1, 15))
        TaskExecution.objects.create(
            task=self.task,
            duration=8,
            day=date(2018, 1, 12))
        TaskExecution.objects.create(
            task=self.task,
            duration=2,
            day=date(2018, 1, 17))

        resp = self.client.get('/task/taskexecution/')
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            3)

        resp = self.client.get('/task/taskexecution/?' + urlencode({
            'max_date': '2018-01-14',
        }))
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            1)
        self.assertSetEqual(
            {ex['day'] for ex in resp.data},
            {
                '2018-01-12',
            })

        resp = self.client.get('/task/taskexecution/?' + urlencode({
            'max_date': '2016-02-14',
        }))
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            0)

    def test_task_execution_min_max_filter(self):
        TaskExecution.objects.create(
            task=self.task,
            duration=4,
            day=date(2018, 1, 15))
        TaskExecution.objects.create(
            task=self.task,
            duration=8,
            day=date(2018, 1, 12))
        TaskExecution.objects.create(
            task=self.task,
            duration=2,
            day=date(2018, 1, 17))

        resp = self.client.get('/task/taskexecution/')
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            3)

        resp = self.client.get('/task/taskexecution/?' + urlencode({
            'min_date': '2018-01-14',
            'max_date': '2018-01-17',
        }))
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            2)
        self.assertSetEqual(
            {ex['day'] for ex in resp.data},
            {
                '2018-01-15',
                '2018-01-17',
            })

        resp = self.client.get('/task/taskexecution/?' + urlencode({
            'min_date': '2018-01-13',
            'max_date': '2018-01-14',
        }))
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            0)

    def test_task_execution_task_filter(self):
        task2 = Task.objects.create(
            user=self.user,
            name='Another Testtask',
            duration=Decimal(4))
        task3 = Task.objects.create(
            user=self.user,
            name='Yet Another Testtask',
            duration=Decimal(5))

        TaskExecution.objects.create(
            task=self.task,
            duration=4,
            day=date(2018, 1, 15))
        TaskExecution.objects.create(
            task=self.task,
            duration=8,
            day=date(2018, 1, 12))
        TaskExecution.objects.create(
            task=self.task,
            duration=2,
            day=date(2018, 1, 17))

        TaskExecution.objects.create(
            task=task2,
            duration=2,
            day=date(2018, 2, 17))
        TaskExecution.objects.create(
            task=task2,
            duration=2,
            day=date(2018, 1, 17))

        TaskExecution.objects.create(
            task=task3,
            duration=2,
            day=date(2019, 12, 24))

        resp = self.client.get('/task/taskexecution/')
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            6)

        resp = self.client.get('/task/taskexecution/?' + urlencode({
            'task_ids': [task2.pk],
        }, True))
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            2)
        self.assertSetEqual(
            {ex['task']['id'] for ex in resp.data},
            {
                task2.pk,
            })

        resp = self.client.get('/task/taskexecution/?' + urlencode({
            'task_ids': [task3.pk, task2.pk],
        }, True))
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            3)
        self.assertSetEqual(
            {ex['task']['id'] for ex in resp.data},
            {
                task2.pk,
                task3.pk,
            })

        resp = self.client.get('/task/taskexecution/?' + urlencode({
            'task_ids': [-100],
        }, True))
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            0)

    def test_task_execution_invalid_filter(self):
        resp = self.client.get('/task/taskexecution/?' + urlencode({
            'task_ids': [
                'not an integer!',
            ],
        }, True))
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {
                'task_ids',
            })

        resp = self.client.get('/task/taskexecution/?' + urlencode({
            'task_ids': [
                'not an integer!',
            ],
            'min_date': 'not a date...',
            'max_date': 'not a date...',
        }, True))
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {
                'task_ids',
                'min_date',
                'max_date',
            })

        resp = self.client.get('/task/taskexecution/?' + urlencode({
            'min_date': '2018-05-12',
            'max_date': 'not a date...',
        }, True))
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {
                'max_date',
            })

        resp = self.client.get('/task/taskexecution/?' + urlencode({
            'min_date': '2018-05-12',
            'max_date': '2018-05-11',  # before min_date
        }, True))
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST,
            'the max date should not be allowed to be before the min date')
        self.assertSetEqual(
            set(resp.data),
            {
                'max_date',
            },
            'the max date should not be allowed to be before the min date')


class TaskTest(TestCase):
    def setUp(self):
        self.user1 = get_user_model().objects.create(
            username='johndoe',
            workhours_weekday=Decimal(10),
            workhours_weekend=Decimal(5),
            default_schedule_duration=Decimal(1),
            default_schedule_full_duration_max=Decimal(3),
        )
        self.user2 = get_user_model().objects.create(
            username='foobar',
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

    def test_incomplete_duration(self):
        task1 = Task.objects.create(user=self.user1, duration=42)
        self.assertEqual(
            task1.incomplete_duration,
            42)
        exec1 = TaskExecution.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=4,
            finished=False)
        self.assertEqual(
            task1.incomplete_duration,
            38)
        exec1.finished = True
        exec1.save()
        self.assertEqual(
            task1.incomplete_duration,
            38)
        exec2 = TaskExecution.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=2,
            finished=False)
        self.assertEqual(
            task1.incomplete_duration,
            36)
        exec2.finished = True
        exec2.save()
        self.assertEqual(
            task1.incomplete_duration,
            36)
        exec1.finished = False
        exec1.save()
        self.assertEqual(
            task1.incomplete_duration,
            36)

    def test_incomplete_tasks(self):
        self.assertEqual(
            set(self.user1.tasks.filter_incomplete()),
            set())
        self.assertEqual(
            set(self.user2.tasks.filter_incomplete()),
            set())
        task1 = Task.objects.create(user=self.user1, duration=2)
        self.assertEqual(
            set(self.user1.tasks.filter_incomplete()),
            {task1})
        self.assertEqual(
            set(self.user2.tasks.filter_incomplete()),
            set())
        exec1 = TaskExecution.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=1,
            finished=False)
        self.assertEqual(
            set(self.user1.tasks.filter_incomplete()),
            {task1})
        self.assertEqual(
            set(self.user2.tasks.filter_incomplete()),
            set())
        exec2 = TaskExecution.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=1,
            finished=False)
        self.assertEqual(
            set(self.user1.tasks.filter_incomplete()),
            set())
        self.assertEqual(
            set(self.user2.tasks.filter_incomplete()),
            set())
        exec2.finished = True
        exec2.save()
        self.assertEqual(
            set(self.user1.tasks.filter_incomplete()),
            set())
        self.assertEqual(
            set(self.user2.tasks.filter_incomplete()),
            set())
        exec1.finished = True
        exec1.save()
        self.assertEqual(
            set(self.user1.tasks.filter_incomplete()),
            set())
        self.assertEqual(
            set(self.user2.tasks.filter_incomplete()),
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
            task1.incomplete_duration,
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
            task1.incomplete_duration,
            Decimal)


class TaskExecutionTest(TestCase):
    def setUp(self):
        self.user1 = get_user_model().objects.create(
            username='johndoe',
            workhours_weekday=Decimal(10),
            workhours_weekend=Decimal(5),
            default_schedule_duration=Decimal(1),
            default_schedule_full_duration_max=Decimal(3),
        )
        self.user2 = get_user_model().objects.create(
            username='foobar',
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

from datetime import date, timedelta
from decimal import Decimal
from io import StringIO
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import call_command
from django.db.models import Q
from django.http import HttpRequest
from django.test import TestCase
from freezegun import freeze_time
from rest_framework import status
from rest_framework.request import Request

from base.tests import AuthenticatedApiTest
from label.models import Label
from .models import Task, TaskChunk, TaskChunkSeries
from .serializers import TaskChunkSeriesSerializer


class ManagementTest(TestCase):
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

    @freeze_time('2010-05-03')
    def test_schedule_task_chunk_series(self):
        task1 = Task.objects.create(
            user=self.user1,
            name='Testtask',
            duration=Decimal(2))
        series1 = TaskChunkSeries.objects.create(
            task=task1,
            start=date(2010, 5, 3),
            duration=Decimal('0.5'),
            rule='interval',
            interval_days=182)  # 3 chunks will be scheduled within the next year

        task2 = Task.objects.create(
            user=self.user1,
            name='Testtask 2',
            duration=Decimal(4))
        series2 = TaskChunkSeries.objects.create(
            task=task2,
            start=date(2011, 4, 3),
            duration=Decimal('2.5'),
            rule='interval',
            interval_days=25)  # 2 chunks will be scheduled within the next year

        task3 = Task.objects.create(
            user=self.user2,
            name='Testtask 3',
            duration=Decimal(4))
        series3 = TaskChunkSeries.objects.create(
            task=task3,
            start=date(2010, 7, 3),
            end=date(2010, 8, 3),
            duration=Decimal('2.5'),
            rule='interval',
            interval_days=1)  # 32 chunks will be scheduled within the next year

        self.assertEqual(
            TaskChunk.objects.count(),
            0)

        out = StringIO()
        call_command('scheduletaskchunkseries', stdout=out)

        self.assertEqual(
            TaskChunk.objects.filter(series=series1).count(),
            3)
        self.assertEqual(
            TaskChunk.objects.filter(series=series2).count(),
            2)
        self.assertEqual(
            TaskChunk.objects.filter(series=series3).count(),
            32)

        self.assertEqual(
            TaskChunk.objects.count(),
            37)

        self.assertIn('scheduled 37 chunks for 3 series', out.getvalue())


class TaskViewSetTest(AuthenticatedApiTest):
    def test_create_task(self):
        """
        Test the creation of a new task.
        """
        resp = self.client.post('/task/task/', {
            'name': 'Testtask',
            'duration': '2.5',
            'priority': 7,
            'start': '2018-05-23',
            'deadline': '2018-05-29',
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
        self.assertEqual(
            task.priority,
            7)
        self.assertEqual(
            task.start,
            date(2018, 5, 23))
        self.assertEqual(
            task.deadline,
            date(2018, 5, 29))

    def test_create_task_invalid_deadline(self):
        """
        Test the creation of a new task with a deadline that is before the start.
        """
        resp = self.client.post('/task/task/', {
            'name': 'Testtask',
            'start': '2018-05-23',
            'deadline': '2018-05-21',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {
                'start',
                'deadline',
            })

        self.assertEqual(
            Task.objects.count(),
            0)

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

    def test_create_task_invalid_priority(self):
        """
        Test the creation of a new task with a deadline that is before the start.
        """
        resp = self.client.post('/task/task/', {
            'name': 'Testtask',
            'priority': -6,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {
                'priority',
            })

        self.assertEqual(
            Task.objects.count(),
            0)

        resp = self.client.post('/task/task/', {
            'name': 'Testtask',
            'priority': 14,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {
                'priority',
            })

        self.assertEqual(
            Task.objects.count(),
            0)

        self.assertEqual(
            Task.objects.count(),
            0)

        resp = self.client.post('/task/task/', {
            'name': 'Testtask',
            'priority': 'not a number',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {
                'priority',
            })

        self.assertEqual(
            Task.objects.count(),
            0)

    def test_create_task_with_labels(self):
        """
        Test the creation of a new task.
        """
        label1 = Label.objects.create(
            user=self.user,
            title='Test Label',
            color='333333')
        label2 = Label.objects.create(
            user=self.user,
            title='Second Label',
            color='003333')

        resp = self.client.post('/task/task/', {
            'name': 'Testtask',
            'duration': '2.5',
            'priority': 7,
            'start': '2018-05-23',
            'deadline': '2018-05-29',
            'labels': [label1.pk, label2.pk],
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
        self.assertEqual(
            task.priority,
            7)
        self.assertEqual(
            task.start,
            date(2018, 5, 23))
        self.assertEqual(
            task.deadline,
            date(2018, 5, 29))
        self.assertEqual(
            set(label.pk for label in task.labels.all()),
            {label1.pk, label2.pk})

        resp = self.client.post('/task/task/', {
            'name': 'Testtask',
            'duration': '2.5',
            'priority': 7,
            'start': '2018-05-23',
            'deadline': '2018-05-29',
            'labels': [label2.pk],
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)

        self.assertEqual(
            Task.objects.count(),
            2)

        task = Task.objects.filter(~Q(pk=task.pk)).first()
        self.assertEqual(
            task.user,
            self.user)
        self.assertEqual(
            task.name,
            'Testtask')
        self.assertEqual(
            task.duration,
            Decimal('2.5'))
        self.assertEqual(
            task.priority,
            7)
        self.assertEqual(
            task.start,
            date(2018, 5, 23))
        self.assertEqual(
            task.deadline,
            date(2018, 5, 29))
        self.assertEqual(
            set(label.pk for label in task.labels.all()),
            {label2.pk})

    def test_update_task_duration_less_than_scheduled(self):
        """
        Test setting the duration of a task that is less than the
        scheduled duration.
        """
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=Decimal(2))
        TaskChunk.objects.create(
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
        TaskChunk.objects.create(
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

    def test_update_task_invalid_start(self):
        """
        Test updating a task to an invalid start.
        """
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=Decimal(2),
            start=date(2018, 5, 23),
            deadline=date(2018, 5, 29))
        resp = self.client.patch('/task/task/{}/'.format(task.pk), {
            'start': '2018-06-10',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {'start'})

        task.refresh_from_db()
        self.assertEqual(
            task.start,
            date(2018, 5, 23))

    def test_partially_update_invalid_task_dates(self):
        """
        Test that it is allowed to update a task that already has an invalid
        start/deadline pair if neither start nor deadline are updated in the
        request.
        """
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=Decimal(2),
            start=date(2018, 5, 30),
            deadline=date(2018, 3, 29))
        resp = self.client.patch('/task/task/{}/'.format(task.pk), {
            'name': 'renamed',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)

        task.refresh_from_db()
        self.assertEqual(
            task.name,
            'renamed')

    def test_update_task_invalid_deadline(self):
        """
        Test updating a task to an invalid deadline.
        """
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=Decimal(2),
            start=date(2018, 5, 23),
            deadline=date(2018, 5, 29))
        resp = self.client.patch('/task/task/{}/'.format(task.pk), {
            'deadline': '2018-05-10',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {'deadline'})

        task.refresh_from_db()
        self.assertEqual(
            task.deadline,
            date(2018, 5, 29))

    def test_update_task_invalid_priority(self):
        """
        Test updating a task to an invalid deadline.
        """
        task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=Decimal(2))
        resp = self.client.patch('/task/task/{}/'.format(task.pk), {
            'priority': 42,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {'priority'})

        task.refresh_from_db()
        self.assertEqual(
            task.priority,
            5,  # default priority
        )

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

    def test_partially_update_task_with_labels(self):
        """
        Test the update of the labels of a task.
        """
        label1 = Label.objects.create(
            user=self.user,
            title='Test Label',
            color='333333')
        label2 = Label.objects.create(
            user=self.user,
            title='Second Label',
            color='003333')

        task = Task.objects.create(
            user=self.user,
            name='Testtask')
        resp = self.client.patch('/task/task/{}/'.format(task.id), {
            'labels': [label1.pk],
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(
            set(label.pk for label in task.labels.all()),
            {label1.pk})

        resp = self.client.patch('/task/task/{}/'.format(task.id), {
            'labels': [],
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(
            set(label.pk for label in task.labels.all()),
            set())

        resp = self.client.patch('/task/task/{}/'.format(task.id), {
            'labels': [label2.pk, label1.pk],
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(
            set(label.pk for label in task.labels.all()),
            {label1.pk, label2.pk})

        resp = self.client.patch('/task/task/{}/'.format(task.id), {
            'labels': [label2.pk],
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(
            set(label.pk for label in task.labels.all()),
            {label2.pk})

        resp = self.client.patch('/task/task/{}/'.format(task.id), {
            'labels': [label1.pk],
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(
            set(label.pk for label in task.labels.all()),
            {label1.pk})

    def test_update_task_with_labels(self):
        """
        Test that PUTting a task without specifying labels does not alter
        the labels.
        """
        label1 = Label.objects.create(
            user=self.user,
            title='Test Label',
            color='333333')
        label2 = Label.objects.create(
            user=self.user,
            title='Second Label',
            color='003333')

        task = Task.objects.create(
            user=self.user,
            name='Testtask')
        task.labels.add(label1)
        task.labels.add(label2)

        resp = self.client.put('/task/task/{}/'.format(task.id), {
            'name': 'Testtask',
            'duration': 5,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(
            set(label.pk for label in task.labels.all()),
            {label1.pk, label2.pk})

        resp = self.client.put('/task/task/{}/'.format(task.id), {
            'name': 'Testtask',
            'duration': 5,
            'labels': [label2.pk],
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(
            set(label.pk for label in task.labels.all()),
            {label2.pk})

        resp = self.client.put('/task/task/{}/'.format(task.id), {
            'name': 'Testtask',
            'duration': 5,
            'labels': [],
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(
            set(label.pk for label in task.labels.all()),
            set())

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
        TaskChunk.objects.create(
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

    def test_merge_task(self):
        task1 = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=Decimal(3))
        task2 = Task.objects.create(
            user=self.user,
            name='To be merged Testtask',
            duration=Decimal(2))

        TaskChunk.objects.create(
            task=task1,
            duration=Decimal(1),
            day=date(2010, 12, 24)),
        TaskChunk.objects.create(
            task=task1,
            duration=Decimal('0.5'),
            day=date(2010, 12, 24)),
        TaskChunk.objects.create(
            task=task1,
            duration=Decimal('0.5'),
            day=date(2010, 12, 24)),

        TaskChunk.objects.create(
            task=task2,
            duration=Decimal('1.5'),
            day=date(2010, 12, 24)),
        TaskChunk.objects.create(
            task=task2,
            duration=Decimal('0.5'),
            day=date(2010, 12, 24)),

        resp = self.client.post('/task/task/{}/merge/{}/'.format(task1.pk, task2.pk))
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            5)
        for chunk in resp.data:
            self.assertEqual(
                chunk['task']['id'],
                task1.pk)

    def test_merge_foreign_task(self):
        task1 = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=Decimal(3))
        task2 = Task.objects.create(
            user=get_user_model().objects.create(username='foreign'),
            name='Foreign Testtask',
            duration=Decimal(2))

        TaskChunk.objects.create(
            task=task1,
            duration=Decimal(1),
            day=date(2010, 12, 24)),
        TaskChunk.objects.create(
            task=task1,
            duration=Decimal('0.5'),
            day=date(2010, 12, 24)),
        TaskChunk.objects.create(
            task=task1,
            duration=Decimal('0.5'),
            day=date(2010, 12, 24)),

        TaskChunk.objects.create(
            task=task2,
            duration=Decimal('1.5'),
            day=date(2010, 12, 24)),
        TaskChunk.objects.create(
            task=task2,
            duration=Decimal('0.5'),
            day=date(2010, 12, 24)),

        resp = self.client.post('/task/task/{}/merge/{}/'.format(task1.pk, task2.pk))
        self.assertEqual(
            resp.status_code,
            status.HTTP_404_NOT_FOUND)


class TaskChunkViewSetTest(AuthenticatedApiTest):
    def setUp(self):
        super().setUp()

        self.day = date(2001, 2, 3)
        self.day2 = date(2001, 2, 4)

        self.task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=Decimal(2))

    def test_split_task_chunk(self):
        """Test splitting a task chunk."""
        chunk = TaskChunk.objects.create(
            task=self.task,
            day=self.day,
            day_order=0,
            duration=Decimal(3))

        resp = self.client.post('/task/chunk/{}/split/'.format(chunk.pk))
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            2)
        resp_chunk = next(filter(lambda item: item['id'] == chunk.id, resp.data))
        self.assertEqual(
            Decimal(resp_chunk['duration']),
            Decimal(1),
            'the original chunk should have a duration of 1')
        resp_new_chunk = next(filter(lambda item: item['id'] != chunk.id, resp.data))
        self.assertEqual(
            Decimal(resp_new_chunk['duration']),
            Decimal(2),
            'the new chunk should have the remaining duration')

        self.assertEqual(
            TaskChunk.objects.count(),
            2)

        chunk.refresh_from_db()
        self.assertEqual(
            chunk.duration,
            Decimal(1))
        self.assertEqual(
            chunk.day_order,
            0)

        new_chunk = TaskChunk.objects.get(~Q(pk=chunk.pk))
        self.assertEqual(
            new_chunk.duration,
            Decimal(2))
        self.assertEqual(
            new_chunk.day_order,
            1)

    def test_split_task_chunk_custom_duration(self):
        """Test splitting a task chunk."""
        chunk = TaskChunk.objects.create(
            task=self.task,
            day=self.day,
            day_order=0,
            duration=Decimal(1))

        resp = self.client.post('/task/chunk/{}/split/?duration=0.3'.format(chunk.pk))
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            2)

        self.assertEqual(
            TaskChunk.objects.count(),
            2)

        chunk.refresh_from_db()
        self.assertEqual(
            chunk.duration,
            Decimal('0.3'))
        self.assertEqual(
            chunk.day_order,
            0)

        new_chunk = TaskChunk.objects.get(~Q(pk=chunk.pk))
        self.assertEqual(
            new_chunk.duration,
            Decimal('0.7'))
        self.assertEqual(
            new_chunk.day_order,
            1)

    def test_split_task_chunk_invalid(self):
        """Test splitting a task chunk."""
        chunk = TaskChunk.objects.create(
            task=self.task,
            day=self.day,
            day_order=0,
            duration=Decimal(1))

        # no duration left for split
        resp = self.client.post('/task/chunk/{}/split/'.format(chunk.pk))
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {'duration'})

        resp = self.client.post('/task/chunk/{}/split/?duration=2'.format(chunk.pk))
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {'duration'})

        resp = self.client.post('/task/chunk/{}/split/?duration=invalid'.format(chunk.pk))
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {'duration'})

        chunk.finished = True
        chunk.save()

        resp = self.client.post('/task/chunk/{}/split/'.format(chunk.pk))
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            resp.data['detail'],
            'finished chunks can not be split')

    def test_finish_task_chunk(self):
        """Test finishing a task chunk."""
        task_chunk = TaskChunk.objects.create(
            task=self.task,
            day=self.day,
            day_order=0,
            duration=Decimal(1))

        self.assertEqual(
            task_chunk.finished,
            False)

        resp = self.client.patch('/task/chunk/{}/'.format(task_chunk.pk), {
            'finished': True,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            Decimal(resp.data['task']['duration']),
            Decimal(2))
        self.assertEqual(
            Decimal(resp.data['task']['scheduled_duration']),
            Decimal(1))
        self.assertEqual(
            Decimal(resp.data['task']['finished_duration']),
            Decimal(1))

        task_chunk.refresh_from_db()
        self.assertEqual(
            task_chunk.finished,
            True)

    def test_unfinish_task_chunk(self):
        """Test unfinishing a task chunk."""
        task_chunk = TaskChunk.objects.create(
            task=self.task,
            day=self.day,
            day_order=0,
            duration=Decimal(1),
            finished=True)

        self.assertEqual(
            task_chunk.finished,
            True)

        resp = self.client.patch('/task/chunk/{}/'.format(task_chunk.pk), {
            'finished': False,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            Decimal(resp.data['task']['duration']),
            Decimal(2))
        self.assertEqual(
            Decimal(resp.data['task']['scheduled_duration']),
            Decimal(1))
        self.assertEqual(
            Decimal(resp.data['task']['finished_duration']),
            Decimal(0))

        task_chunk.refresh_from_db()
        self.assertEqual(
            task_chunk.finished,
            False)

    def test_delete_task_chunk(self):
        """Test the deletion of a task chunk without postponing."""
        task_chunk = TaskChunk.objects.create(
            task=self.task,
            day=self.day,
            day_order=0,
            duration=Decimal(1))

        resp = self.client.delete('/task/chunk/{}/?postpone=0'.format(task_chunk.pk))
        self.assertEqual(
            resp.status_code,
            status.HTTP_204_NO_CONTENT)

        self.assertRaises(
            ObjectDoesNotExist,
            task_chunk.refresh_from_db)
        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            Decimal(1))

    def test_delete_task_chunk_with_task(self):
        """
        Test the deletion of a task chunk without postponing.

        The task should be deleted as well because the task chunk
        duration matches the task duration.
        """
        task_chunk = TaskChunk.objects.create(
            task=self.task,
            day=self.day,
            day_order=0,
            duration=Decimal(2))

        resp = self.client.delete('/task/chunk/{}/?postpone=0'.format(task_chunk.pk))
        self.assertEqual(
            resp.status_code,
            status.HTTP_204_NO_CONTENT)

        self.assertRaises(
            ObjectDoesNotExist,
            task_chunk.refresh_from_db)
        self.assertRaises(
            ObjectDoesNotExist,
            self.task.refresh_from_db)

    def test_postpone_task_chunk(self):
        """Test the deletion of a task chunk with postponing."""
        task_chunk = TaskChunk.objects.create(
            task=self.task,
            day=self.day,
            day_order=0,
            duration=Decimal(1))

        resp = self.client.delete('/task/chunk/{}/?postpone=1'.format(task_chunk.pk))
        self.assertEqual(
            resp.status_code,
            status.HTTP_204_NO_CONTENT)

        self.assertRaises(
            ObjectDoesNotExist,
            task_chunk.refresh_from_db)
        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            Decimal(2))

    def test_change_duration(self):
        """
        Test changing the duration of the task chunk.
        This should change the task duration as well.
        """
        task_chunk = TaskChunk.objects.create(
            task=self.task,
            day=self.day,
            day_order=0,
            duration=Decimal(1),
            finished=True)

        self.assertEqual(
            task_chunk.finished,
            True)

        resp = self.client.patch('/task/chunk/{}/'.format(task_chunk.pk), {
            'duration': 4,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            Decimal(resp.data['task']['duration']),
            Decimal(5))
        self.assertEqual(
            Decimal(resp.data['task']['scheduled_duration']),
            Decimal(4))
        self.assertEqual(
            Decimal(resp.data['task']['finished_duration']),
            Decimal(4))

        task_chunk.refresh_from_db()
        self.assertEqual(
            task_chunk.duration,
            Decimal(4))
        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            Decimal(5))  # 2 + (4 - 1)

        resp = self.client.patch('/task/chunk/{}/'.format(task_chunk.pk), {
            'duration': '0.5',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)

        task_chunk.refresh_from_db()
        self.assertEqual(
            task_chunk.duration,
            Decimal('0.5'))
        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            Decimal('1.5'))  # 5 + (0.5 - 4)

    def test_change_duration_invalid(self):
        """
        Test changing the duration of the task chunk to an invalid value.
        """
        task_chunk = TaskChunk.objects.create(
            task=self.task,
            day=self.day,
            day_order=0,
            duration=Decimal(1),
            finished=True)

        self.assertEqual(
            task_chunk.finished,
            True)

        resp = self.client.patch('/task/chunk/{}/'.format(task_chunk.pk), {
            'duration': -4,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)

        task_chunk.refresh_from_db()
        self.assertEqual(
            task_chunk.duration,
            Decimal(1))

    def test_exchange_task_chunk(self):
        """Test exchanging a task chunk with another."""
        task_chunk1 = TaskChunk.objects.create(
            task=self.task,
            day=self.day,
            duration=Decimal(1),
            day_order=1
        )
        task_chunk2 = TaskChunk.objects.create(
            task=self.task,
            day=self.day,
            duration=Decimal(1),
            day_order=2
        )

        resp = self.client.patch('/task/chunk/{}/'.format(task_chunk1.pk), {
            'day_order': 2,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        task_chunk1.refresh_from_db()
        self.assertEqual(
            task_chunk1.day_order,
            2)
        task_chunk2.refresh_from_db()
        self.assertEqual(
            task_chunk2.day_order,
            1)

        resp = self.client.put('/task/chunk/{}/'.format(task_chunk1.pk), {
            'task_id': self.task.id,
            'day': '2001-02-03',
            'duration': 1,
            'day_order': 1,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        task_chunk1.refresh_from_db()
        self.assertEqual(
            task_chunk1.day_order,
            1)
        task_chunk2.refresh_from_db()
        self.assertEqual(
            task_chunk2.day_order,
            2)

    def test_exchange_task_chunk_different_day(self):
        """Test exchanging a task chunk with another."""
        task_chunk1 = TaskChunk.objects.create(
            task=self.task,
            day=self.day,
            duration=Decimal(1),
            day_order=1
        )
        task_chunk2 = TaskChunk.objects.create(
            task=self.task,
            day=self.day,
            duration=Decimal(1),
            day_order=2
        )
        task_chunk3 = TaskChunk.objects.create(
            task=self.task,
            day=self.day,
            duration=Decimal(1),
            day_order=3
        )
        task_chunk4 = TaskChunk.objects.create(
            task=self.task,
            day=self.day,
            duration=Decimal(1),
            day_order=4
        )
        task_chunk5 = TaskChunk.objects.create(
            task=self.task,
            day=self.day2,
            duration=Decimal(1),
            day_order=1
        )

        resp = self.client.patch('/task/chunk/{}/'.format(task_chunk5.pk), {
            'day_order': 3,
            'day': self.day,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)

        task_chunk5.refresh_from_db()
        self.assertEqual(
            task_chunk5.day,
            self.day)
        self.assertEqual(
            task_chunk5.day_order,
            5)

        task_chunk1.refresh_from_db()
        self.assertEqual(
            task_chunk1.day_order,
            1)
        task_chunk2.refresh_from_db()
        self.assertEqual(
            task_chunk2.day_order,
            2)
        task_chunk3.refresh_from_db()
        self.assertEqual(
            task_chunk3.day_order,
            3)
        task_chunk4.refresh_from_db()
        self.assertEqual(
            task_chunk4.day_order,
            4)

    def test_task_chunk_change_day(self):
        """
        Test changing the day of a task chunk. The submitted
        day order should be ignored and the chunk placed at the
        end of the new day.
        """
        task_chunk1 = TaskChunk.objects.create(
            task=self.task,
            day=self.day,
            duration=Decimal(1),
            day_order=1
        )
        task_chunk2 = TaskChunk.objects.create(
            task=self.task,
            day=self.day2,
            duration=Decimal(1),
            day_order=1
        )

        resp = self.client.patch('/task/chunk/{}/'.format(task_chunk1.pk), {
            'day': '2001-02-04',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        task_chunk1.refresh_from_db()
        self.assertEqual(
            task_chunk1.day_order,
            2)
        self.assertEqual(
            task_chunk1.day,
            self.day2)
        task_chunk2.refresh_from_db()
        self.assertEqual(
            task_chunk2.day_order,
            1)

        # provided day order should be ignored
        resp = self.client.put('/task/chunk/{}/'.format(task_chunk1.pk), {
            'task_id': self.task.id,
            'day': '2001-02-01',
            'duration': 1,
            'day_order': 42,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        task_chunk1.refresh_from_db()
        self.assertEqual(
            task_chunk1.day_order,
            1)
        self.assertEqual(
            task_chunk1.day,
            date(2001, 2, 1))
        task_chunk2.refresh_from_db()
        self.assertEqual(
            task_chunk2.day_order,
            1)

        resp = self.client.patch('/task/chunk/{}/'.format(task_chunk1.pk), {
            'day': '2001-02-01',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        task_chunk1.refresh_from_db()
        self.assertEqual(
            task_chunk1.day_order,
            1)
        self.assertEqual(
            task_chunk1.day,
            date(2001, 2, 1))

    def test_explicit_creation(self):
        """
        Test the explicit creation of a new task chunk.
        """
        resp = self.client.post('/task/chunk/', {
            'task_id': self.task.id,
            'day': '2001-02-03',
            'day_order': 0,
            'duration': 2,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_chunk = TaskChunk.objects.get(
            pk=resp.data['id'])
        self.assertEqual(
            task_chunk.task,
            self.task)
        self.assertEqual(
            task_chunk.day,
            self.day)
        self.assertEqual(
            task_chunk.day_order,
            0)
        self.assertEqual(
            task_chunk.duration,
            Decimal(2))

        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            Decimal(2))

    def test_explicit_creation_task_duration_increase(self):
        """
        Test the explicit creation of a new task chunk with a duration longer
        than the task duration. The task duration should be increased.
        """
        resp = self.client.post('/task/chunk/', {
            'task_id': self.task.id,
            'day': '2001-02-03',
            'day_order': 0,
            'duration': 5,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_chunk = TaskChunk.objects.get(
            pk=resp.data['id'])
        self.assertEqual(
            task_chunk.task,
            self.task)
        self.assertEqual(
            task_chunk.day,
            self.day)
        self.assertEqual(
            task_chunk.day_order,
            0)
        self.assertEqual(
            task_chunk.duration,
            Decimal(5))

        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            Decimal(5))

    def test_explicit_creation_day_order(self):
        """
        Test that the day order is set correctly when explicitly
        creating multiple task chunks without specifying a day order.
        """
        resp = self.client.post('/task/chunk/', {
            'task_id': self.task.id,
            'day': '2001-02-03',
            'duration': '0.5',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_chunk1 = TaskChunk.objects.get(
            pk=resp.data['id'])

        resp = self.client.post('/task/chunk/', {
            'task_id': self.task.id,
            'day': '2001-02-04',
            'duration': '0.5',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_chunk2 = TaskChunk.objects.get(
            pk=resp.data['id'])

        resp = self.client.post('/task/chunk/', {
            'task_id': self.task.id,
            'day': '2001-02-03',
            'duration': '0.1',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_chunk3 = TaskChunk.objects.get(
            pk=resp.data['id'])

        resp = self.client.post('/task/chunk/', {
            'task_id': self.task.id,
            'day': '2001-02-03',
            'duration': '0.1',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_chunk4 = TaskChunk.objects.get(
            pk=resp.data['id'])

        self.assertGreater(
            task_chunk4.day_order,
            task_chunk3.day_order,
            task_chunk1.day_order)

        # both task chunks were the first of their day
        self.assertEqual(
            task_chunk1.day_order,
            task_chunk2.day_order)

    def test_explicit_creation_too_high_duration(self):
        """
        Explicitly create a new task chunk.
        Try to set the duration higher than the incomplete duration of
        the task.
        The task duration should be increased in that case.
        """
        TaskChunk.objects.create(
            task=self.task,
            day=self.day,
            duration=Decimal(1),
            finished=True)

        resp = self.client.post('/task/chunk/', {
            'task_id': self.task.id,
            'day': '2001-02-03',
            'duration': 5,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_chunk = TaskChunk.objects.get(
            pk=resp.data['id'])
        self.assertEqual(
            task_chunk.task,
            self.task)
        self.assertEqual(
            task_chunk.day,
            self.day)
        self.assertEqual(
            task_chunk.duration,
            Decimal(5))

        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            Decimal(6))  # 1 + (5 - 1)

    @freeze_time('2001-02-03')
    def test_schedule_for_today(self):
        """Test scheduling for current day."""
        resp = self.client.post('/task/chunk/', {
            'task_id': self.task.id,
            'day': 'today',
            'duration': 2,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_chunk = TaskChunk.objects.get(
            pk=resp.data['id'])
        self.assertEqual(
            task_chunk.task,
            self.task)
        self.assertEqual(
            task_chunk.day,
            self.day)
        self.assertEqual(
            task_chunk.duration,
            Decimal(2))

        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            Decimal(2))

    @freeze_time('2001-02-03')
    def test_schedule_for_tomorrow(self):
        """Test scheduling for the next day."""
        resp = self.client.post('/task/chunk/', {
            'task_id': self.task.id,
            'day': 'tomorrow',
            'duration': 2,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_chunk = TaskChunk.objects.get(
            pk=resp.data['id'])
        self.assertEqual(
            task_chunk.task,
            self.task)
        self.assertEqual(
            task_chunk.day,
            self.day + timedelta(days=1))
        self.assertEqual(
            task_chunk.duration,
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
        TaskChunk.objects.create(
            task=task2,
            day=self.day,  # Saturday
            duration=Decimal(5))
        TaskChunk.objects.create(
            task=task2,
            day=self.day + timedelta(days=1),  # Sunday
            duration=Decimal(5))
        TaskChunk.objects.create(
            task=task2,
            day=self.day + timedelta(days=2),  # Monday
            duration=Decimal(7))

        self.task.duration = 10
        self.task.save()

        resp = self.client.post('/task/chunk/', {
            'task_id': self.task.id,
            'day': 'next_free_capacity',
            'duration': 9,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_chunk = TaskChunk.objects.get(
            pk=resp.data['id'])
        self.assertEqual(
            task_chunk.task,
            self.task)
        self.assertEqual(
            task_chunk.day,
            self.day + timedelta(days=3))  # Tuesday
        self.assertEqual(
            task_chunk.duration,
            Decimal(9))

        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            Decimal(10))

    @freeze_time('2001-02-03')
    def test_schedule_next_free_capacity_exact(self):
        """
        Test scheduling for the next free capacity when the chunk fits
        exactly into a day.
        """
        task2 = Task.objects.create(
            user=self.user,
            name='Other Testtask',
            duration=Decimal(30))
        TaskChunk.objects.create(
            task=task2,
            day=self.day,  # Saturday
            duration=Decimal(5))
        TaskChunk.objects.create(
            task=task2,
            day=self.day + timedelta(days=1),  # Sunday
            duration=Decimal(5))
        TaskChunk.objects.create(
            task=task2,
            day=self.day + timedelta(days=2),  # Monday
            duration=Decimal(7))

        self.task.duration = self.user.workhours_weekday
        self.task.save()

        resp = self.client.post('/task/chunk/', {
            'task_id': self.task.id,
            'day': 'next_free_capacity',
            'duration': self.user.workhours_weekday,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)
        task_chunk = TaskChunk.objects.get(
            pk=resp.data['id'])
        self.assertEqual(
            task_chunk.task,
            self.task)
        self.assertEqual(
            task_chunk.day,
            self.day + timedelta(days=3))  # Tuesday
        self.assertEqual(
            task_chunk.duration,
            self.user.workhours_weekday)

        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            Decimal(10))

    @freeze_time('2001-02-03')
    def test_schedule_next_free_capacity_unavailable(self):
        """Test scheduling for the next free capacity."""
        task2 = Task.objects.create(
            user=self.user,
            name='Other Testtask',
            duration=Decimal(30))
        for offset in range(100):
            day = self.day + timedelta(days=offset)
            TaskChunk.objects.create(
                task=task2,
                day=day,
                duration=self.user.capacity_of_day(day))

        self.task.duration = 10
        self.task.save()

        resp = self.client.post('/task/chunk/', {
            'task_id': self.task.id,
            'day': 'next_free_capacity',
            'duration': 5,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {'day'})

    @freeze_time('2001-02-03')
    def test_schedule_next_free_capacity_too_long(self):
        """Test scheduling for the next free capacity."""
        self.task.duration = 25
        self.task.save()

        resp = self.client.post('/task/chunk/', {
            'task_id': self.task.id,
            'day': 'next_free_capacity',
            'duration': 25,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {'day'})

    def test_schedule_invalid(self):
        """Test scheduling for the next free capacity."""
        task2 = Task.objects.create(
            user=self.user,
            name='Other Testtask',
            duration=Decimal(30))
        TaskChunk.objects.create(
            task=task2,
            day=self.day,  # Saturday
            duration=Decimal(5))
        TaskChunk.objects.create(
            task=task2,
            day=self.day + timedelta(days=1),  # Sunday
            duration=Decimal(5))
        TaskChunk.objects.create(
            task=task2,
            day=self.day + timedelta(days=2),  # Monday
            duration=Decimal(7))

        self.task.duration = 10
        self.task.save()

        resp = self.client.post('/task/chunk/', {
            'task_id': task2.pk,
            'day': 'next_free_capacity',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {'day'})

        resp = self.client.post('/task/chunk/', {
            'day': 'next_free_capacity',
            'duration': 9,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {'task_id', 'day'})

        resp = self.client.post('/task/chunk/', {
            'task_id': -100,
            'day': 'next_free_capacity',
            'duration': 9,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {'task_id', 'day'})

        resp = self.client.post('/task/chunk/', {
            'task_id': self.task.pk,
            'day': 'next_free_capacity',
            'duration': 'not a decimal',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_400_BAD_REQUEST)
        self.assertSetEqual(
            set(resp.data),
            {'day', 'duration'})

    def test_task_chunk_nonstrict_date_filter(self):
        """
        Test that unfinished chunks from days prior to min_date are
        included without strict date filtering.
        """
        TaskChunk.objects.create(
            task=self.task,
            duration=4,
            day=date(2018, 1, 15))
        TaskChunk.objects.create(
            task=self.task,
            duration=8,
            day=date(2018, 1, 12),
            finished=True)
        TaskChunk.objects.create(
            task=self.task,
            duration=2,
            day=date(2018, 1, 17),
            finished=True)

        resp = self.client.get('/task/chunk/')
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            3)

        resp = self.client.get('/task/chunk/?' + urlencode({
            'min_date': '2018-01-16',
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

        resp = self.client.get('/task/chunk/?' + urlencode({
            'min_date': '2018-02-14',
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
                '2018-01-15',
            })

    def test_task_chunk_strict_date_filter(self):
        """
        Test that unfinished chunks from days prior to min_date are
        not included with strict date filtering.
        """
        TaskChunk.objects.create(
            task=self.task,
            duration=4,
            day=date(2018, 1, 15))
        TaskChunk.objects.create(
            task=self.task,
            duration=8,
            day=date(2018, 1, 12),
            finished=True)
        TaskChunk.objects.create(
            task=self.task,
            duration=2,
            day=date(2018, 1, 17),
            finished=True)

        resp = self.client.get('/task/chunk/?' + urlencode({
            'strict_date': True,
        }))
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            3)

        resp = self.client.get('/task/chunk/?' + urlencode({
            'min_date': '2018-01-16',
            'strict_date': True,
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
                '2018-01-17',
            })

        resp = self.client.get('/task/chunk/?' + urlencode({
            'min_date': '2018-02-14',
            'strict_date': True,
        }))
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            0)

    def test_task_chunk_min_filter(self):
        TaskChunk.objects.create(
            task=self.task,
            duration=4,
            day=date(2018, 1, 15),
            finished=True)
        TaskChunk.objects.create(
            task=self.task,
            duration=8,
            day=date(2018, 1, 12),
            finished=True)
        TaskChunk.objects.create(
            task=self.task,
            duration=2,
            day=date(2018, 1, 17),
            finished=True)

        resp = self.client.get('/task/chunk/')
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            3)

        resp = self.client.get('/task/chunk/?' + urlencode({
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

        resp = self.client.get('/task/chunk/?' + urlencode({
            'min_date': '2018-02-14',
        }))
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            0)

    def test_task_chunk_max_filter(self):
        TaskChunk.objects.create(
            task=self.task,
            duration=4,
            day=date(2018, 1, 15))
        TaskChunk.objects.create(
            task=self.task,
            duration=8,
            day=date(2018, 1, 12))
        TaskChunk.objects.create(
            task=self.task,
            duration=2,
            day=date(2018, 1, 17))

        resp = self.client.get('/task/chunk/')
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            3)

        resp = self.client.get('/task/chunk/?' + urlencode({
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

        resp = self.client.get('/task/chunk/?' + urlencode({
            'max_date': '2016-02-14',
        }))
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            0)

    def test_task_chunk_min_max_filter(self):
        TaskChunk.objects.create(
            task=self.task,
            duration=4,
            day=date(2018, 1, 15),
            finished=True)
        TaskChunk.objects.create(
            task=self.task,
            duration=8,
            day=date(2018, 1, 12),
            finished=True)
        TaskChunk.objects.create(
            task=self.task,
            duration=2,
            day=date(2018, 1, 17),
            finished=True)

        resp = self.client.get('/task/chunk/')
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            3)

        resp = self.client.get('/task/chunk/?' + urlencode({
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

        resp = self.client.get('/task/chunk/?' + urlencode({
            'min_date': '2018-01-13',
            'max_date': '2018-01-14',
        }))
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            0)

    def test_task_chunk_task_filter(self):
        task2 = Task.objects.create(
            user=self.user,
            name='Another Testtask',
            duration=Decimal(4))
        task3 = Task.objects.create(
            user=self.user,
            name='Yet Another Testtask',
            duration=Decimal(5))

        TaskChunk.objects.create(
            task=self.task,
            duration=4,
            day=date(2018, 1, 15))
        TaskChunk.objects.create(
            task=self.task,
            duration=8,
            day=date(2018, 1, 12))
        TaskChunk.objects.create(
            task=self.task,
            duration=2,
            day=date(2018, 1, 17))

        TaskChunk.objects.create(
            task=task2,
            duration=2,
            day=date(2018, 2, 17))
        TaskChunk.objects.create(
            task=task2,
            duration=2,
            day=date(2018, 1, 17))

        TaskChunk.objects.create(
            task=task3,
            duration=2,
            day=date(2019, 12, 24))

        resp = self.client.get('/task/chunk/')
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            6)

        resp = self.client.get('/task/chunk/?' + urlencode({
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

        resp = self.client.get('/task/chunk/?' + urlencode({
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

        resp = self.client.get('/task/chunk/?' + urlencode({
            'task_ids': [-100],
        }, True))
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK)
        self.assertEqual(
            len(resp.data),
            0)

    def test_task_chunk_invalid_filter(self):
        resp = self.client.get('/task/chunk/?' + urlencode({
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

        resp = self.client.get('/task/chunk/?' + urlencode({
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

        resp = self.client.get('/task/chunk/?' + urlencode({
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

        resp = self.client.get('/task/chunk/?' + urlencode({
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

    def test_str(self):
        task = Task(user=self.user1, name='Testtask')
        self.assertEqual(
            str(task),
            'johndoe: Testtask')

    def test_state(self):
        task = Task.objects.create(user=self.user1, duration=10)
        self.assertFalse(task.completely_scheduled)
        self.assertFalse(task.finished)
        chunk1 = TaskChunk.objects.create(
            task=task,
            day=self.weekdaydate1,
            day_order=0,
            duration=4,
            finished=False)
        self.assertFalse(task.completely_scheduled)
        self.assertFalse(task.finished)
        TaskChunk.objects.create(
            task=task,
            day=self.weekdaydate1 + timedelta(days=1),
            day_order=0,
            duration=6,
            finished=True)
        self.assertTrue(task.completely_scheduled)
        self.assertFalse(task.finished)
        chunk1.finished = True
        chunk1.save()
        self.assertTrue(task.completely_scheduled)
        self.assertTrue(task.finished)

    def test_finished_duration(self):
        task1 = Task.objects.create(user=self.user1, duration=42)
        self.assertEqual(
            task1.finished_duration,
            0)
        chunk1 = TaskChunk.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=4,
            finished=False)
        self.assertEqual(
            task1.finished_duration,
            0)
        chunk1.finished = True
        chunk1.save()
        self.assertEqual(
            task1.finished_duration,
            4)
        chunk2 = TaskChunk.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=2,
            finished=False)
        self.assertEqual(
            task1.finished_duration,
            4)
        chunk2.finished = True
        chunk2.save()
        self.assertEqual(
            task1.finished_duration,
            6)
        chunk1.finished = False
        chunk1.save()
        self.assertEqual(
            task1.finished_duration,
            2)

    def test_unfinished_duration(self):
        task1 = Task.objects.create(user=self.user1, duration=42)
        self.assertEqual(
            task1.unfinished_duration,
            Decimal(42))
        chunk1 = TaskChunk.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=4,
            finished=False)
        self.assertEqual(
            task1.unfinished_duration,
            Decimal(42))
        chunk1.finished = True
        chunk1.save()
        self.assertEqual(
            task1.unfinished_duration,
            Decimal(38))
        chunk2 = TaskChunk.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=2,
            finished=False)
        self.assertEqual(
            task1.unfinished_duration,
            Decimal(38))
        chunk2.finished = True
        chunk2.save()
        self.assertEqual(
            task1.unfinished_duration,
            Decimal(36))
        chunk1.finished = False
        chunk1.save()
        self.assertEqual(
            task1.unfinished_duration,
            Decimal(40))

    def test_scheduled_duration(self):
        task1 = Task.objects.create(user=self.user1, duration=42)
        self.assertEqual(
            task1.scheduled_duration,
            0)
        chunk1 = TaskChunk.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=4,
            finished=False)
        self.assertEqual(
            task1.scheduled_duration,
            4)
        chunk1.finished = True
        chunk1.save()
        self.assertEqual(
            task1.scheduled_duration,
            4)
        chunk2 = TaskChunk.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=2,
            finished=False)
        self.assertEqual(
            task1.scheduled_duration,
            6)
        chunk2.finished = True
        chunk2.save()
        self.assertEqual(
            task1.scheduled_duration,
            6)
        chunk1.finished = False
        chunk1.save()
        self.assertEqual(
            task1.scheduled_duration,
            6)

    def test_unscheduled_duration(self):
        task1 = Task.objects.create(user=self.user1, duration=42)
        self.assertEqual(
            task1.unscheduled_duration,
            42)
        chunk1 = TaskChunk.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=4,
            finished=False)
        self.assertEqual(
            task1.unscheduled_duration,
            38)
        chunk1.finished = True
        chunk1.save()
        self.assertEqual(
            task1.unscheduled_duration,
            38)
        chunk2 = TaskChunk.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=2,
            finished=False)
        self.assertEqual(
            task1.unscheduled_duration,
            36)
        chunk2.finished = True
        chunk2.save()
        self.assertEqual(
            task1.unscheduled_duration,
            36)
        chunk1.finished = False
        chunk1.save()
        self.assertEqual(
            task1.unscheduled_duration,
            36)

    def test_incompletely_scheduled_tasks(self):
        self.assertEqual(
            set(self.user1.tasks.incompletely_scheduled()),
            set())
        self.assertEqual(
            set(self.user2.tasks.incompletely_scheduled()),
            set())
        task1 = Task.objects.create(user=self.user1, duration=2)
        self.assertEqual(
            set(self.user1.tasks.incompletely_scheduled()),
            {task1})
        self.assertEqual(
            set(self.user2.tasks.incompletely_scheduled()),
            set())
        chunk1 = TaskChunk.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=1,
            finished=False)
        self.assertEqual(
            set(self.user1.tasks.incompletely_scheduled()),
            {task1})
        self.assertEqual(
            set(self.user2.tasks.incompletely_scheduled()),
            set())
        chunk2 = TaskChunk.objects.create(
            task=task1,
            day=self.weekdaydate1,
            day_order=0,
            duration=1,
            finished=False)
        self.assertEqual(
            set(self.user1.tasks.incompletely_scheduled()),
            set())
        self.assertEqual(
            set(self.user2.tasks.incompletely_scheduled()),
            set())
        chunk2.finished = True
        chunk2.save()
        self.assertEqual(
            set(self.user1.tasks.incompletely_scheduled()),
            set())
        self.assertEqual(
            set(self.user2.tasks.incompletely_scheduled()),
            set())
        chunk1.finished = True
        chunk1.save()
        self.assertEqual(
            set(self.user1.tasks.incompletely_scheduled()),
            set())
        self.assertEqual(
            set(self.user2.tasks.incompletely_scheduled()),
            set())

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
        TaskChunk.objects.create(
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

    def test_merge_tasks(self):
        task1 = Task.objects.create(
            user=self.user1,
            name='Testtask',
            duration=Decimal(3))
        task2 = Task.objects.create(
            user=self.user1,
            name='To be merged Testtask',
            duration=Decimal(2))

        chunks = [
            TaskChunk.objects.create(
                task=task1,
                duration=Decimal(1),
                day=self.weekdaydate1),
            TaskChunk.objects.create(
                task=task1,
                duration=Decimal('0.5'),
                day=self.weekdaydate1),
            TaskChunk.objects.create(
                task=task1,
                duration=Decimal('0.5'),
                day=self.weekdaydate1),

            TaskChunk.objects.create(
                task=task2,
                duration=Decimal('1.5'),
                day=self.weekdaydate1),
            TaskChunk.objects.create(
                task=task2,
                duration=Decimal('0.5'),
                day=self.weekdaydate1),
        ]

        affected_chunks = task1.merge(task2)
        self.assertSetEqual(
            set(affected_chunks),
            set(chunks))

        for chunk in affected_chunks:
            self.assertEqual(
                chunk.task,
                task1)

        for chunk in chunks:
            chunk.refresh_from_db()
            self.assertEqual(
                chunk.task,
                task1)

        # task 2 should not exist anymore
        self.assertRaises(
            ObjectDoesNotExist,
            task2.refresh_from_db)

        task1.refresh_from_db()
        self.assertEqual(
            task1.name,
            'Testtask')
        self.assertEqual(
            task1.duration,
            Decimal(5))

    def test_merge_tasks_no_chunks(self):
        task1 = Task.objects.create(
            user=self.user1,
            name='Testtask',
            duration=Decimal(3))
        task2 = Task.objects.create(
            user=self.user1,
            name='To be merged Testtask',
            duration=Decimal(2))

        affected_chunks = task1.merge(task2)
        self.assertSetEqual(
            set(affected_chunks),
            set())

        # task 2 should not exist anymore
        self.assertRaises(
            ObjectDoesNotExist,
            task2.refresh_from_db)

        task1.refresh_from_db()
        self.assertEqual(
            task1.name,
            'Testtask')
        self.assertEqual(
            task1.duration,
            Decimal(5))

    def test_merge_tasks_invalid(self):
        task1 = Task.objects.create(
            user=self.user1,
            name='Testtask',
            duration=Decimal(3))
        task2 = Task.objects.create(
            user=self.user2,
            name='To be merged Testtask',
            duration=Decimal(2))

        # can't merge tasks of different users
        self.assertRaises(
            AssertionError,
            task1.merge,
            task2)

        # can't merge task with itself
        self.assertRaises(
            AssertionError,
            task1.merge,
            task1)


class TaskChunkSeriesTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(
            username='johndoe',
            workhours_weekday=Decimal(10),
            workhours_weekend=Decimal(5),
            default_schedule_duration=Decimal(1),
            default_schedule_full_duration_max=Decimal(3),
        )
        self.task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=Decimal(1))

    def test_str(self):
        series = TaskChunkSeries(
            task=self.task,
            rule='interval')
        self.assertEqual(
            str(series),
            'johndoe: Testtask: interval')

    def test_add_months(self):
        self.assertEqual(
            TaskChunkSeries._add_months(
                date(2010, 7, 15),
                3),
            date(2010, 10, 15))

        self.assertEqual(
            TaskChunkSeries._add_months(
                date(2010, 7, 15),
                12),
            date(2011, 7, 15))

        self.assertEqual(
            TaskChunkSeries._add_months(
                date(2010, 7, 15),
                17),
            date(2011, 12, 15))

    def test_advance_to_weekday(self):
        self.assertEqual(
            TaskChunkSeries._advance_to_weekday(
                date(2010, 7, 5),
                3),
            date(2010, 7, 8))

        self.assertEqual(
            TaskChunkSeries._advance_to_weekday(
                date(2010, 7, 8),
                3),
            date(2010, 7, 8))

        self.assertEqual(
            TaskChunkSeries._advance_to_weekday(
                date(2010, 7, 9),
                3),
            date(2010, 7, 15))

    def test_replace_day(self):
        self.assertEqual(
            TaskChunkSeries._replace_day(
                date(2010, 7, 15),
                3),
            date(2010, 7, 3))

        self.assertEqual(
            TaskChunkSeries._replace_day(
                date(2012, 2, 15),
                31),
            date(2012, 2, 29))

        self.assertEqual(
            TaskChunkSeries._replace_day(
                date(2012, 2, 15),
                30),
            date(2012, 2, 29))

        self.assertEqual(
            TaskChunkSeries._replace_day(
                date(2011, 2, 15),
                30),
            date(2011, 2, 28))

    def test_apply_rule_interval(self):
        series = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 24),
            rule='interval',
            interval_days=10)

        # interval without previous occurrence schedules for start
        self.assertEqual(
            series.apply_rule(),
            series.start)

        self.assertEqual(
            series.apply_rule(date(2010, 3, 16)),
            date(2010, 3, 26))

        self.assertEqual(
            series.apply_rule(date(2010, 3, 26)),
            date(2010, 4, 5))

    def test_apply_rule_interval_before_start(self):
        series = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 12, 24),
            end=date(2011, 12, 24),
            rule='interval',
            interval_days=10)

        # last before start is ignored
        self.assertEqual(
            series.apply_rule(date(2005, 3, 26)),
            series.start)

    def test_apply_rule_interval_end(self):
        series = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 24),
            end=date(2010, 12, 24),
            rule='interval',
            interval_days=10)

        # exactly on end date
        self.assertEqual(
            series.apply_rule(date(2010, 12, 14)),
            date(2010, 12, 24))

        # would be after end date
        self.assertEqual(
            series.apply_rule(date(2010, 12, 15)),
            None)
        self.assertEqual(
            series.apply_rule(date(2010, 12, 24)),
            None)

    def test_apply_rule_monthly(self):
        series = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 7),
            rule='monthly',
            monthly_day=7,
            monthly_months=1)

        # interval without previous occurrence schedules for month of start
        self.assertEqual(
            series.apply_rule(),
            date(2010, 2, 7))

        self.assertEqual(
            series.apply_rule(date(2010, 3, 16)),
            date(2010, 4, 7))

        self.assertEqual(
            series.apply_rule(date(2010, 3, 5)),
            date(2010, 4, 7))

    def test_apply_rule_monthly_last(self):
        series = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 28),
            rule='monthly',
            monthly_day=31,
            monthly_months=1)

        # interval without previous occurrence schedules for month of start
        self.assertEqual(
            series.apply_rule(),
            date(2010, 2, 28))

        self.assertEqual(
            series.apply_rule(date(2010, 3, 16)),
            date(2010, 4, 30))

        self.assertEqual(
            series.apply_rule(date(2010, 3, 5)),
            date(2010, 4, 30))

        self.assertEqual(
            series.apply_rule(date(2012, 1, 5)),
            date(2012, 2, 29))

        self.assertEqual(
            series.apply_rule(date(2012, 9, 5)),
            date(2012, 10, 31))

    def test_apply_rule_monthly_before_start(self):
        series = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 7),
            rule='monthly',
            monthly_day=7,
            monthly_months=1)

        # last before start is ignored
        self.assertEqual(
            series.apply_rule(date(2009, 10, 5)),
            date(2010, 2, 7))

    def test_apply_rule_monthly_end(self):
        series = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 24),
            end=date(2010, 12, 24),
            rule='monthly',
            monthly_day=24,
            monthly_months=1)

        # exactly on end date
        self.assertEqual(
            series.apply_rule(date(2010, 11, 7)),
            series.end)

        series.end = date(2010, 12, 23)
        series.save()
        # would be after end date
        self.assertEqual(
            series.apply_rule(date(2010, 12, 1)),
            None)
        self.assertEqual(
            series.apply_rule(date(2010, 11, 24)),
            None)

    def test_apply_rule_multiple_monthly(self):
        series = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 24),
            rule='monthly',
            monthly_day=24,
            monthly_months=4)

        # interval without previous occurrence schedules for month of start
        self.assertEqual(
            series.apply_rule(),
            date(2010, 2, 24))

        series.start = date(2010, 2, 5)
        series.save()
        self.assertEqual(
            series.apply_rule(),
            date(2010, 2, 24))

        self.assertEqual(
            series.apply_rule(date(2010, 3, 7)),
            date(2010, 7, 24))

        self.assertEqual(
            series.apply_rule(date(2010, 11, 18)),
            date(2011, 3, 24))

    def test_apply_rule_multi_monthly_verylong(self):
        """
        Test for correct behaviour when using a very long interval.
        """
        series = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 24),
            rule='monthly',
            monthly_day=24,
            monthly_months=120)  # 10 years

        self.assertEqual(
            series.apply_rule(date(2010, 3, 7)),
            date(2020, 3, 24))

        self.assertEqual(
            series.apply_rule(date(2010, 11, 18)),
            date(2020, 11, 24))

    def test_apply_rule_multi_monthly_before_start(self):
        series = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 24),
            rule='monthly',
            monthly_day=24,
            monthly_months=4)

        # last before start is ignored
        self.assertEqual(
            series.apply_rule(date(2009, 10, 5)),
            date(2010, 2, 24))

    def test_apply_rule_multi_monthly_end(self):
        series = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 24),
            end=date(2010, 12, 24),
            rule='monthly',
            monthly_day=24,
            monthly_months=4)

        # exactly on end date
        self.assertEqual(
            series.apply_rule(date(2010, 8, 24)),
            series.end)

        series.end = date(2010, 12, 23)
        series.save()
        # would be after end date
        self.assertEqual(
            series.apply_rule(date(2010, 8, 24)),
            None)

    def test_apply_rule_monthlyweekday_1st(self):
        series = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 1),
            rule='monthlyweekday',
            monthly_months=1,
            monthlyweekday_weekday=5,
            monthlyweekday_nth=1)

        # interval without previous occurrence schedules for month of start
        self.assertEqual(
            series.apply_rule(),
            date(2010, 2, 6))

        self.assertEqual(
            series.apply_rule(date(2010, 3, 16)),
            date(2010, 4, 3))

        self.assertEqual(
            series.apply_rule(date(2010, 3, 5)),
            date(2010, 4, 3))

        self.assertEqual(
            series.apply_rule(date(2010, 5, 16)),
            date(2010, 6, 5))

    def test_apply_rule_monthlyweekday_2nd(self):
        series = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 1),
            rule='monthlyweekday',
            monthly_months=1,
            monthlyweekday_weekday=5,
            monthlyweekday_nth=2)

        # interval without previous occurrence schedules for month of start
        self.assertEqual(
            series.apply_rule(),
            date(2010, 2, 13))

        self.assertEqual(
            series.apply_rule(date(2010, 3, 16)),
            date(2010, 4, 10))

        self.assertEqual(
            series.apply_rule(date(2010, 3, 5)),
            date(2010, 4, 10))

        self.assertEqual(
            series.apply_rule(date(2010, 5, 16)),
            date(2010, 6, 12))

    def test_apply_rule_monthlyweekday_last(self):
        series = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 1),
            rule='monthlyweekday',
            monthly_months=1,
            monthlyweekday_weekday=5,
            monthlyweekday_nth=6)

        # interval without previous occurrence schedules for month of start
        self.assertEqual(
            series.apply_rule(),
            date(2010, 2, 27))

        self.assertEqual(
            series.apply_rule(date(2010, 3, 16)),
            date(2010, 4, 24))

        self.assertEqual(
            series.apply_rule(date(2010, 3, 5)),
            date(2010, 4, 24))

        self.assertEqual(
            series.apply_rule(date(2010, 5, 16)),
            date(2010, 6, 26))

    def test_schedule_limit_count(self):
        series = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 24),
            rule='interval',
            interval_days=10)

        self.assertEqual(
            TaskChunk.objects.count(),
            0)

        scheduled = series.schedule(max_count=5)
        self.assertEqual(
            len(scheduled),
            5)
        self.assertEqual(
            TaskChunk.objects.count(),
            5)

        scheduled = series.schedule(max_count=5)
        self.assertEqual(
            len(scheduled),
            5)
        self.assertEqual(
            TaskChunk.objects.count(),
            10)

    def test_schedule_limit_advance(self):
        series = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 24),
            rule='interval',
            interval_days=10)

        self.assertEqual(
            TaskChunk.objects.count(),
            0)

        with freeze_time('2010-02-24'):
            scheduled = series.schedule(max_advance=timedelta(days=10))
        self.assertEqual(
            len(scheduled),
            2)
        self.assertEqual(
            TaskChunk.objects.count(),
            2)

        with freeze_time('2010-03-06'):
            scheduled = series.schedule(max_advance=timedelta(days=10))
        self.assertEqual(
            len(scheduled),
            1)
        self.assertEqual(
            TaskChunk.objects.count(),
            3)
        self.assertSetEqual(
            set(chunk['day'] for chunk in TaskChunk.objects.values('day')),
            {
                date(2010, 2, 24),
                date(2010, 2, 24) + timedelta(days=10),
                date(2010, 2, 24) + timedelta(days=20),
            })

    def test_schedule_end(self):
        series = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 24),
            end=date(2010, 4, 24),
            rule='interval',
            interval_days=7)

        self.assertEqual(
            TaskChunk.objects.count(),
            0)

        scheduled = series.schedule()
        self.assertEqual(
            len(scheduled),
            9)
        self.assertEqual(
            TaskChunk.objects.count(),
            9)

        scheduled = series.schedule(max_advance=timedelta(days=10))
        self.assertEqual(
            len(scheduled),
            0)
        self.assertEqual(
            TaskChunk.objects.count(),
            9)
        self.assertSetEqual(
            set(chunk['day'] for chunk in TaskChunk.objects.values('day')),
            {
                date(2010, 2, 24) + timedelta(days=7 * n)
                for n in range(9)
            })

    @freeze_time('2010-02-24')
    def test_schedule_infinite(self):
        series = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 24),
            rule='interval',
            interval_days=7)

        self.assertEqual(
            TaskChunk.objects.count(),
            0)

        for n in range(10):
            scheduled = series.schedule(max_advance=timedelta(days=3650))
            self.assertEqual(
                len(scheduled),
                50)
            self.assertEqual(
                TaskChunk.objects.count(),
                50 * (n + 1))

        self.assertSetEqual(
            set(chunk['day'] for chunk in TaskChunk.objects.values('day')),
            {
                date(2010, 2, 24) + timedelta(days=7 * n)
                for n in range(10 * 50)
            })

    def test_schedule_increases_task_duration(self):
        """
        Test that newly scheduled task chunks increase the task
        duration.
        """
        initial_task_duration = self.task.duration

        series = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 24),
            rule='interval',
            interval_days=7)
        scheduled = series.schedule(max_advance=timedelta(days=3650))
        self.assertEqual(
            len(scheduled),
            50)

        self.task.refresh_from_db()
        self.assertEqual(
            self.task.duration,
            initial_task_duration + series.duration * 50)


class TaskChunkSeriesSerializerTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(
            username='johndoe',
            workhours_weekday=Decimal(10),
            workhours_weekend=Decimal(5),
            default_schedule_duration=Decimal(1),
            default_schedule_full_duration_max=Decimal(3),
        )
        self.task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=Decimal(1))

        # we need an authenticated request
        self.request = Request(HttpRequest())
        self.request.user = self.user

        self.context = {
            'request': self.request,
        }

    def test_validation_invalid_rule(self):
        serializer = TaskChunkSeriesSerializer(data={
            'task_id': self.task.pk,
            'start': '2010-05-03',
            'rule': 'invalid',
        }, context=self.context)
        self.assertFalse(
            serializer.is_valid())
        self.assertSetEqual(
            set(serializer.errors.keys()),
            {'rule'})

    def test_validation_interval(self):
        serializer = TaskChunkSeriesSerializer(data={
            'task_id': self.task.pk,
            'start': '2010-05-03',
            'rule': 'interval',
            # interval_days missing
        }, context=self.context)
        self.assertFalse(
            serializer.is_valid())
        self.assertSetEqual(
            set(serializer.errors.keys()),
            {'interval_days'})

        serializer = TaskChunkSeriesSerializer(data={
            'task_id': self.task.pk,
            'start': '2010-05-03',
            'rule': 'interval',
            'interval_days': 7,

            # fields for other rules
            'monthly_day': 17,
            'monthly_months': 1,
            'monthlyweekday_weekday': 0,
            'monthlyweekday_nth': 2,
        }, context=self.context)
        self.assertFalse(
            serializer.is_valid())
        self.assertSetEqual(
            set(serializer.errors.keys()),
            {
                'monthly_day',
                'monthly_months',
                'monthlyweekday_weekday',
                'monthlyweekday_nth'
            })

        serializer = TaskChunkSeriesSerializer(data={
            'task_id': self.task.pk,
            'start': '2010-05-03',
            'rule': 'interval',
            'interval_days': 7,
        }, context=self.context)
        self.assertTrue(
            serializer.is_valid())

    def test_validation_monthly(self):
        serializer = TaskChunkSeriesSerializer(data={
            'task_id': self.task.pk,
            'start': '2010-05-03',
            'rule': 'monthly',
            # monthly_day missing
            # monthly_months missing
        }, context=self.context)
        self.assertFalse(
            serializer.is_valid())
        self.assertSetEqual(
            set(serializer.errors.keys()),
            {
                'monthly_day',
                'monthly_months',
            })

        serializer = TaskChunkSeriesSerializer(data={
            'task_id': self.task.pk,
            'start': '2010-05-03',
            'rule': 'monthly',
            'monthly_day': 3,
            'monthly_months': 1,

            # fields for other rules
            'interval_days': 7,
            'monthlyweekday_weekday': 0,
            'monthlyweekday_nth': 2,
        }, context=self.context)
        self.assertFalse(
            serializer.is_valid())
        self.assertSetEqual(
            set(serializer.errors.keys()),
            {
                'interval_days',
                'monthlyweekday_weekday',
                'monthlyweekday_nth',
            })

        serializer = TaskChunkSeriesSerializer(data={
            'task_id': self.task.pk,
            'start': '2010-05-03',
            'rule': 'monthly',
            'monthly_day': 7,  # not the same day as start date
            'monthly_months': 1,
        }, context=self.context)
        self.assertFalse(
            serializer.is_valid())
        self.assertSetEqual(
            set(serializer.errors.keys()),
            {'monthly_day'})

        serializer = TaskChunkSeriesSerializer(data={
            'task_id': self.task.pk,
            'start': '2010-05-03',
            'rule': 'monthly',
            'monthly_day': 3,
            'monthly_months': 1,
        }, context=self.context)

        self.assertTrue(
            serializer.is_valid())

    def test_validation_monthly_last_day_of_month(self):
        serializer = TaskChunkSeriesSerializer(data={
            'task_id': self.task.pk,
            'start': '2010-01-31',
            'rule': 'monthly',
            'monthly_day': 31,
            'monthly_months': 1,
        }, context=self.context)
        self.assertTrue(
            serializer.is_valid())

        serializer = TaskChunkSeriesSerializer(data={
            'task_id': self.task.pk,
            'start': '2010-02-28',
            'rule': 'monthly',
            'monthly_day': 31,  # not the same as start date, but end of month
            'monthly_months': 1,
        }, context=self.context)
        self.assertTrue(
            serializer.is_valid())

        serializer = TaskChunkSeriesSerializer(data={
            'task_id': self.task.pk,
            'start': '2008-02-29',  # lap year
            'rule': 'monthly',
            'monthly_day': 31,  # not the same as start date, but end of month
            'monthly_months': 1,
        }, context=self.context)
        self.assertTrue(
            serializer.is_valid())

        serializer = TaskChunkSeriesSerializer(data={
            'task_id': self.task.pk,
            'start': '2010-04-30',
            'rule': 'monthly',
            'monthly_day': 31,  # not the same as start date, but end of month
            'monthly_months': 1,
        }, context=self.context)

        self.assertTrue(
            serializer.is_valid())

        serializer = TaskChunkSeriesSerializer(data={
            'task_id': self.task.pk,
            'start': '2010-01-30',
            'rule': 'monthly',
            'monthly_day': 31,  # not the same as start date and not end of month
            'monthly_months': 1,
        }, context=self.context)
        self.assertFalse(
            serializer.is_valid())
        self.assertSetEqual(
            set(serializer.errors.keys()),
            {'monthly_day'})

    def test_validation_monthlyweekday(self):
        serializer = TaskChunkSeriesSerializer(data={
            'task_id': self.task.pk,
            'start': '2010-05-03',
            'rule': 'monthlyweekday',
            # monthly_months missing
            # monthlyweekday_weekday missing
            # monthlyweekday_nth missing
        }, context=self.context)
        self.assertFalse(
            serializer.is_valid())
        self.assertSetEqual(
            set(serializer.errors.keys()),
            {
                'monthly_months',
                'monthlyweekday_weekday',
                'monthlyweekday_nth',
            })

        serializer = TaskChunkSeriesSerializer(data={
            'task_id': self.task.pk,
            'start': '2010-05-03',
            'rule': 'monthlyweekday',
            'monthly_months': 1,
            'monthlyweekday_weekday': 0,
            'monthlyweekday_nth': 2,

            # fields for other rules
            'interval_days': 7,
            'monthly_day': 7,
        }, context=self.context)
        self.assertFalse(
            serializer.is_valid())
        self.assertSetEqual(
            set(serializer.errors.keys()),
            {
                'interval_days',
                'monthly_day',
            })

        serializer = TaskChunkSeriesSerializer(data={
            'task_id': self.task.pk,
            'start': '2010-05-03',
            'rule': 'monthlyweekday',
            'monthly_months': 1,
            'monthlyweekday_weekday': 0,
            'monthlyweekday_nth': 2,
        }, context=self.context)
        self.assertTrue(
            serializer.is_valid())

    def test_update_interval(self):
        instance = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 24),
            rule='interval',
            interval_days=10)

        serializer = TaskChunkSeriesSerializer(instance=instance, data={
            'task_id': self.task.pk,
            'start': '2010-02-24',
            'rule': 'interval',
            'interval_days': 7,
        }, context=self.context)
        self.assertTrue(
            serializer.is_valid())
        serializer.save()
        instance.refresh_from_db()
        self.assertEqual(
            instance.task,
            self.task)
        self.assertEqual(
            instance.start,
            date(2010, 2, 24))
        self.assertEqual(
            instance.rule,
            'interval')
        self.assertEqual(
            instance.interval_days,
            7)

    def test_validation_update_change_rule(self):
        instance = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 24),
            rule='interval',
            interval_days=10)

        serializer = TaskChunkSeriesSerializer(instance=instance, data={
            'task_id': self.task.pk,
            'start': '2010-02-24',
            'rule': 'monthly',
            'monthly_day': 15,
            'monthly_months': 2,
        }, context=self.context)
        self.assertFalse(
            serializer.is_valid())
        self.assertSetEqual(
            set(serializer.errors.keys()),
            {'rule'})
        self.assertRaises(
            AssertionError,
            serializer.save)

    def test_validation_update_change_start(self):
        instance = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 24),
            rule='interval',
            interval_days=10)

        serializer = TaskChunkSeriesSerializer(instance=instance, data={
            'task_id': self.task.pk,
            'start': '2010-02-14',
            'rule': 'interval',
            'interval_days': 10,
        }, context=self.context)
        self.assertFalse(
            serializer.is_valid())
        self.assertSetEqual(
            set(serializer.errors.keys()),
            {'start'})
        self.assertRaises(
            AssertionError,
            serializer.save)

    def test_validation_update_change_task(self):
        instance = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 24),
            rule='interval',
            interval_days=10)

        task2 = Task.objects.create(
            user=self.user,
            name='Second Testtask',
            duration=Decimal(1))

        serializer = TaskChunkSeriesSerializer(instance=instance, data={
            'task_id': task2.pk,
            'start': '2010-02-24',
            'rule': 'interval',
            'interval_days': 10,
        }, context=self.context)
        self.assertFalse(
            serializer.is_valid())
        self.assertSetEqual(
            set(serializer.errors.keys()),
            {'task_id'})
        self.assertRaises(
            AssertionError,
            serializer.save)

    def test_validation_update_change_end(self):
        instance = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 24),
            rule='interval',
            interval_days=10)

        serializer = TaskChunkSeriesSerializer(instance=instance, data={
            'task_id': self.task.pk,
            'start': '2010-02-24',
            'end': '2010-05-01',
            'rule': 'interval',
            'interval_days': 10,
        }, context=self.context)
        self.assertTrue(
            serializer.is_valid())
        serializer.save()
        instance.refresh_from_db()
        self.assertEqual(
            instance.start,
            date(2010, 2, 24))
        self.assertEqual(
            instance.end,
            date(2010, 5, 1))

    def test_validation_create_start_after_end(self):
        serializer = TaskChunkSeriesSerializer(data={
            'task_id': self.task.pk,
            'start': '2010-02-24',
            'end': '2010-01-01',
            'rule': 'interval',
            'interval_days': 10,
        }, context=self.context)
        self.assertFalse(
            serializer.is_valid())
        self.assertSetEqual(
            set(serializer.errors.keys()),
            {
                'start',
                'end',
            })

    def test_validation_update_start_after_end(self):
        instance = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 24),
            rule='interval',
            interval_days=10)

        serializer = TaskChunkSeriesSerializer(instance=instance, data={
            'task_id': self.task.pk,
            'start': '2010-02-24',
            'end': '2010-01-01',
            'rule': 'interval',
            'interval_days': 10,
        }, context=self.context)
        self.assertFalse(
            serializer.is_valid())
        self.assertSetEqual(
            set(serializer.errors.keys()),
            {
                'start',
                'end',
            })


class TaskChunkSeriesViewSetTest(AuthenticatedApiTest):
    def setUp(self):
        super().setUp()

        self.task = Task.objects.create(
            user=self.user,
            name='Testtask',
            duration=Decimal(2))

    @freeze_time('2010-05-03')
    def test_defined_ids(self):
        """
        Test that the scheduled chunks returned from the API contain id values.
        This test *will fail* on database backends that are not supported,
        such as sqlite.
        """
        self.assertEqual(
            TaskChunkSeries.objects.count(),
            0)
        self.assertEqual(
            TaskChunk.objects.count(),
            0)

        resp = self.client.post('/task/chunk/series/', {
            'task_id': self.task.pk,
            'duration': '2',
            'start': '2010-05-23',
            'end': '2010-06-23',
            'rule': 'interval',
            'interval_days': 1,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)

        self.assertSetEqual(
            set(resp.data.keys()),
            {'series', 'scheduled'})

        self.assertEqual(
            len(resp.data['scheduled']),
            32)

        for scheduled in resp.data['scheduled']:
            self.assertIsNotNone(scheduled['id'])
            self.assertIsInstance(scheduled['id'], int)

    @freeze_time('2010-05-03')
    def test_create(self):
        """
        Test the creation of a series, making sure that initial
        task chunks are scheduled and returned.
        """
        self.assertEqual(
            TaskChunkSeries.objects.count(),
            0)
        self.assertEqual(
            TaskChunk.objects.count(),
            0)

        resp = self.client.post('/task/chunk/series/', {
            'task_id': self.task.pk,
            'duration': '2',
            'start': '2010-05-23',
            'end': '2010-06-23',
            'rule': 'interval',
            'interval_days': 1,
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_201_CREATED)

        self.assertSetEqual(
            set(resp.data.keys()),
            {'series', 'scheduled'})

        self.assertEqual(
            resp.data['series']['task_id'],
            self.task.pk)
        self.assertEqual(
            Decimal(resp.data['series']['duration']),
            Decimal(2))
        self.assertEqual(
            resp.data['series']['start'],
            '2010-05-23')
        self.assertEqual(
            resp.data['series']['end'],
            '2010-06-23')
        self.assertEqual(
            resp.data['series']['rule'],
            'interval')
        self.assertEqual(
            resp.data['series']['interval_days'],
            1)

        self.assertEqual(
            len(resp.data['scheduled']),
            32)

        self.assertEqual(
            TaskChunkSeries.objects.count(),
            1)
        series = TaskChunkSeries.objects.first()
        self.assertTrue(
            series.completely_scheduled)

        self.assertEqual(
            TaskChunk.objects.count(),
            32)

    def test_partial_update(self):
        """
        Test that it is not allowed to partially update a task chunk series.
        """
        series = TaskChunkSeries.objects.create(
            task=self.task,
            start=date(2010, 2, 24),
            rule='interval',
            interval_days=7)

        resp = self.client.patch('/task/chunk/series/{}/'.format(series.pk), {
            'duration': '2.5',
        })
        self.assertEqual(
            resp.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_no_getting_of_foreign(self):
        foreign_user = get_user_model().objects.create(
            username='foreign')
        foreign_task = Task.objects.create(
            user=foreign_user,
            name='Testtask',
            duration=Decimal(2))
        series = TaskChunkSeries.objects.create(
            task=foreign_task,
            start=date(2010, 2, 24),
            rule='interval',
            interval_days=7)
        resp = self.client.get('/task/chunk/series/{}/'.format(series.id))
        self.assertEqual(
            resp.status_code,
            status.HTTP_404_NOT_FOUND)


class TaskChunkTest(TestCase):
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

    def test_str(self):
        task = Task.objects.create(
            name='Testtask',
            user=self.user1)

        chunk = TaskChunk(task=task, day=date(2018, 12, 24))
        self.assertEqual(
            str(chunk),
            'johndoe: Testtask: 2018-12-24')

    def test_split_chunk(self):
        """
        Test splitting a task chunk.
        """
        task = Task.objects.create(
            name='Testtask',
            user=self.user1,
            duration=5)

        chunk = TaskChunk.objects.create(
            task=task,
            day=date(2018, 12, 24),
            duration=3,
            day_order=0)

        self.assertEqual(
            TaskChunk.objects.count(),
            1)

        affected_chunks = chunk.split()
        self.assertEqual(
            len(affected_chunks),
            2)

        self.assertEqual(
            TaskChunk.objects.count(),
            2)

        chunk.refresh_from_db()
        split_chunk = TaskChunk.objects.get(~Q(pk=chunk.pk))

        self.assertEqual(
            chunk.day_order,
            0)
        self.assertEqual(
            chunk.duration,
            Decimal(1))
        self.assertEqual(
            split_chunk.day_order,
            1)
        self.assertEqual(
            split_chunk.duration,
            Decimal(2))

    def test_split_chunk_with_existing(self):
        """
        Test splitting a task chunk.
        """
        task = Task.objects.create(
            name='Testtask',
            user=self.user1,
            duration=5)
        task2 = Task.objects.create(
            name='Other Testtask',
            user=self.user1,
            duration=5)
        task3 = Task.objects.create(
            name='Yet Other Testtask',
            user=self.user1,
            duration=5)

        chunk0 = TaskChunk.objects.create(
            task=task2,
            day=date(2018, 12, 24),
            duration=3,
            day_order=0)

        chunk = TaskChunk.objects.create(
            task=task,
            day=date(2018, 12, 24),
            duration=3,
            day_order=1)

        chunk2 = TaskChunk.objects.create(
            task=task3,
            day=date(2018, 12, 24),
            duration=3,
            day_order=2)

        chunk3 = TaskChunk.objects.create(
            task=task3,
            day=date(2018, 12, 24),
            duration=3,
            day_order=3)

        self.assertEqual(
            TaskChunk.objects.count(),
            4)

        affected_chunks = chunk.split()
        self.assertEqual(
            len(affected_chunks),
            4)  # first chunk is not affected

        self.assertEqual(
            TaskChunk.objects.count(),
            5)

        chunk0.refresh_from_db()
        chunk.refresh_from_db()
        chunk2.refresh_from_db()
        chunk3.refresh_from_db()
        split_chunk = TaskChunk.objects.get(
            ~Q(pk__in={
                chunk0.pk, chunk.pk, chunk2.pk, chunk3.pk
            }))

        self.assertEqual(
            chunk0.day_order,
            0)
        self.assertEqual(
            chunk2.day_order,
            3)
        self.assertEqual(
            chunk3.day_order,
            4)

        self.assertEqual(
            chunk.day_order,
            1)
        self.assertEqual(
            chunk.duration,
            Decimal(1))
        self.assertEqual(
            split_chunk.day_order,
            2)
        self.assertEqual(
            split_chunk.duration,
            Decimal(2))

    @freeze_time('2017-11-16')
    def test_missed_task_chunks(self):
        self.assertListEqual(
            list(TaskChunk.missed_chunks(self.user1)),
            [])
        self.assertListEqual(
            list(TaskChunk.missed_chunks(self.user2)),
            [])

        task1 = Task.objects.create(
            user=self.user1,
            duration=Decimal(42))

        self.assertListEqual(
            list(TaskChunk.missed_chunks(self.user1)),
            [])
        self.assertListEqual(
            list(TaskChunk.missed_chunks(self.user2)),
            [])

        TaskChunk.objects.create(
            task=task1,
            duration=1,
            day=date(2018, 1, 1),
            day_order=1,
        )

        self.assertListEqual(
            list(TaskChunk.missed_chunks(self.user1)),
            [])
        self.assertListEqual(
            list(TaskChunk.missed_chunks(self.user2)),
            [])

        chunk2 = TaskChunk.objects.create(
            task=task1,
            duration=1,
            day=date(2017, 1, 1),
            day_order=1,
        )

        self.assertListEqual(
            list(TaskChunk.missed_chunks(self.user1)),
            [chunk2])
        self.assertListEqual(
            list(TaskChunk.missed_chunks(self.user2)),
            [])

        chunk3 = TaskChunk.objects.create(
            task=task1,
            duration=1,
            day=date(2015, 5, 1),
            day_order=1,
        )
        self.assertListEqual(
            list(TaskChunk.missed_chunks(self.user1)),
            [chunk3, chunk2])
        self.assertListEqual(
            list(TaskChunk.missed_chunks(self.user2)),
            [])

        chunk3.finished = True
        chunk3.save(update_fields=('finished',))
        self.assertListEqual(
            list(TaskChunk.missed_chunks(self.user1)),
            [chunk2])
        self.assertListEqual(
            list(TaskChunk.missed_chunks(self.user2)),
            [])
        chunk2.finished = True
        chunk2.save(update_fields=('finished',))
        self.assertListEqual(
            list(TaskChunk.missed_chunks(self.user1)),
            [])
        self.assertListEqual(
            list(TaskChunk.missed_chunks(self.user2)),
            [])

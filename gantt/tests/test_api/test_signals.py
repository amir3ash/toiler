import datetime

from django.test import TestCase
from gantt.models import Activity, Project, Task
from user.models import User


class Test(TestCase):
    today = datetime.datetime.now(tz=datetime.timezone.utc)

    def setUp(self) -> None:
        today = self.today
        user = User.objects.create(first_name='user', username='user', email='', password='')
        project = Project.objects.create(
            name='project',
            planned_start_date=today,
            planned_end_date=today,
            actual_start_date=today,
            actual_end_date=today,
            description='',
            project_manager=user
        )
        self.task = Task.objects.create(
            name='task',
            planned_start_date=today,
            planned_end_date=today,
            actual_start_date=today,
            actual_end_date=today,
            description='its task',
            planned_budget=30,
            actual_budget=221,
            project=project
        )

    def test_delete_activity(self):
        today = self.today
        activity = Activity(
            name='name',
            planned_start_date=today,
            planned_end_date=today,
            actual_start_date=today,
            actual_end_date=today,
            description='""""""""""""""""""',
            planned_budget=3,
            actual_budget=2.5,
            task=self.task
        )
        activity.save()

        activity.delete()

from django.contrib.auth.models import User
from rest_framework.test import APITestCase
# from django.contrib.auth import get_user_model

from gantt.models import Project, Task, Activity
from gantt.tests.base import Timer

# User = get_user_model()
timer = Timer()


class TestBench(APITestCase):
    fixtures = ['dumpdata.json']

    # def tearDown(self) -> None:
    # print(self.times)

    # @classmethod
    # def how_are_you(cls):
    #
    # with timer.measure('json_load'), open('/home/amir/Downloads/mockturtle2.json') as f:
    #     data = json.load(f)
    #
    # timer.start('user_bulk_create')
    # users = data[1]
    # User.objects.bulk_create(
    #     [
    #         User(
    #             id=i,
    #             first_name=users[i].get('fist_name'),
    #             last_name=users[i].get('last_name'),
    #             username=users[i].get('username') + str(i),
    #             email=users[i].get('email'),
    #             password='PASSWORD'
    #         )
    #         for i in range(len(users))
    #     ]
    # )
    #
    # timer.stop('user_bulk_create')
    #
    # projects = []
    # tasks = []
    # activities = []
    # timer.start('creating_models')
    # for project, project_id in zip(data[0], range(1, len(data[0]))):
    #     projects.append(
    #         Project(
    #             name=project.get('name'),
    #             planed_start_date=datetime.utcfromtimestamp(project['planed_start_date'] / 10),
    #             planed_end_date=datetime.utcfromtimestamp(project['planned_end_date']),
    #             actual_start_date=datetime.utcfromtimestamp(project['actual_start_date']),
    #             actual_end_date=datetime.utcfromtimestamp(project['actual_end_date']),
    #             description=project['description']
    #         )
    #     )
    #
    #     for task, task_id in zip(project['tasks'], range(1, len(project['tasks']))):
    #         tasks.append(
    #             Task(
    #                 name=task['name'],
    #                 priority=task['priority'],
    #                 planed_start_date=datetime.fromtimestamp(task['planed_start_date'] / 10, timezone.utc),
    #                 planed_end_date=datetime.fromtimestamp(task['planned_end_date'], timezone.utc),
    #                 actual_start_date=datetime.fromtimestamp(task['actual_start_date'], timezone.utc),
    #                 actual_end_date=datetime.fromtimestamp(task['actual_end_date'], timezone.utc),
    #                 description=task['description'],
    #                 planed_budget=task['planned_budget'],
    #                 actual_budget=task['actual_budget'],
    #                 project_id=project_id
    #             )
    #         )
    #
    #         for activity in task['activities']:
    #             activities.append(
    #                 Activity(
    #                     name=activity['name'],
    #                     priority=activity['priority'],
    #                     planed_start_date=datetime.fromtimestamp(activity['planed_start_date'] / 10, timezone.utc),
    #                     planed_end_date=datetime.fromtimestamp(activity['planned_end_date'], timezone.utc),
    #                     actual_start_date=datetime.fromtimestamp(activity['actual_start_date'], timezone.utc),
    #                     actual_end_date=datetime.fromtimestamp(activity['actual_end_date'], timezone.utc),
    #                     description=activity['description'],
    #                     planed_budget=activity['planned_budget'],
    #                     actual_budget=activity['actual_budget'],
    #                     task_id=task_id
    #                 )
    #             )
    #
    # timer.stop('creating_models')
    #
    # with timer.measure('bulk_insert_all'):
    #     timer.start('bulk_insert_project')
    #
    #     Project.objects.bulk_create(projects)
    #
    #     timer.stop('bulk_insert_project')
    #     timer.start('bulk_insert_task')
    #
    #     Task.objects.bulk_create(tasks)
    #
    #     timer.stop('bulk_insert_task')
    #     timer.start('bulk_insert_activity')
    #
    #     Activity.objects.bulk_create(activities)
    #
    #     timer.stop('bulk_insert_activity')
    #
    # cls.times = {'setup_data': {**timer.timers}}
    # timer.timers.clear()

    @classmethod
    @timer.measure('load_data')
    def setUpClass(cls):
        # url = reverse('project_all-detail', kwargs={'pk': 1})
        cls.url = '/gantt/all/1/'
        super().setUpClass()

    @timer.measure('get_count_of_models')
    def test_a(self):
        print("len <'users' 'projects' 'tasks' 'activities'>: ", User.objects.count(), Project.objects.count(),
              Task.objects.count(),
              Activity.objects.count())

    @timer.measure('hello')
    def test_speed(self):
        self.client.force_login(User.objects.get(id=8))
        self.client.get(self.url)
        # print(response.data)


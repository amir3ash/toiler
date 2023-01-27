import datetime

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from gantt.models import Task, Role, Team, TeamMember, Project, State, Activity
from gantt.serializers import ActivitySerializer
from gantt.tests.base import GanttMixin, _create_user


class TestActivityCreate(GanttMixin, APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse('gantt:activity-list')

        cls.test_user2 = _create_user('t2')
        cls.just_authenticated = _create_user('just')

        # create projects
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        cls.project1 = Project.objects.create(name='First Project', planned_start_date=now, planned_end_date=now,
                                              actual_start_date=now, actual_end_date=now, project_manager=cls.user)
        cls.project2 = Project.objects.create(name='Second Project', planned_start_date=now, planned_end_date=now,
                                              actual_start_date=now, actual_end_date=now, project_manager=cls.user)
        cls.project_for_usrname1 = Project.objects.create(name='Project for username1', planned_start_date=now,
                                                          planned_end_date=now, actual_start_date=now,
                                                          actual_end_date=now, project_manager=cls.username1)
        cls.project_for_test_user2 = Project.objects.create(name='nothing', planned_start_date=now,
                                                            planned_end_date=now,
                                                            actual_start_date=now, actual_end_date=now,
                                                            project_manager=cls.test_user2)

        # create teams
        cls.team1 = Team.objects.create(name='First Team', project=cls.project1)
        cls.team2 = Team.objects.create(name='Second Team', project=cls.project1)
        cls.team3 = Team.objects.create(name='3rd Team for project2', project=cls.project2)
        cls.team_for_username1 = Team.objects.create(name='Team for username1 project',
                                                     project=cls.project_for_usrname1)

        # create roles
        cls.role1 = Role.objects.create(name='First role', project=cls.project1)
        cls.role2 = Role.objects.create(name='Second role', project=cls.project1)
        cls.role3 = Role.objects.create(name='3rd role', project=cls.project2)
        cls.role_for_username1 = Role.objects.create(name='4th role', project=cls.project_for_usrname1)

        # create team-members
        cls.member1 = TeamMember.objects.create(team=cls.team1, user=cls.username1, role=cls.role1)
        cls.member2 = TeamMember.objects.create(team=cls.team2, user=cls.username1, role=cls.role1)
        cls.member3 = TeamMember.objects.create(team=cls.team3, user=cls.username1, role=cls.role3)
        cls.member_u1 = TeamMember.objects.create(team=cls.team_for_username1, user=cls.user,
                                                  role=cls.role_for_username1)
        cls.test_user2_member = TeamMember.objects.create(team=cls.team1, user=cls.test_user2, role=cls.role1)

        # create states
        cls.state1 = State.objects.create(name='state1', project=cls.project1)
        cls.state2 = State.objects.create(name='state2', project=cls.project1)
        cls.state3 = State.objects.create(name='state3', project=cls.project2)
        cls.state_for_username1 = State.objects.create(name='s for u1', project=cls.project_for_usrname1)
        cls.state_for_test_user2 = State.objects.create(name='s for test u2', project=cls.project_for_test_user2)

        # create tasks
        cls.task1 = Task.objects.create(name='task1', project=cls.project1, planned_start_date=now,
                                        planned_end_date=now + datetime.timedelta(days=2),
                                        planned_budget=1, actual_budget=4)

        cls.task2 = Task.objects.create(name='task2', project=cls.project1, planned_start_date=now,
                                        planned_end_date=now + datetime.timedelta(days=2),
                                        planned_budget=0, actual_start_date=now - datetime.timedelta(hours=1),
                                        actual_end_date=now, actual_budget=4)

        cls.task3 = Task.objects.create(name='task3', project=cls.project2, planned_start_date=now,
                                        planned_end_date=now + datetime.timedelta(weeks=4), planned_budget=11.5,
                                        actual_start_date=now, actual_budget=0.6)

        cls.task_u1 = Task.objects.create(name='task_u1', project=cls.project_for_usrname1, planned_start_date=now,
                                          planned_end_date=now + datetime.timedelta(days=5), planned_budget=10.15,
                                          actual_budget=0.25)  # A task for the user 'username1'

        cls.task_test_user = Task.objects.create(name='task_test_u', project=cls.project_for_test_user2,
                                                 planned_start_date=now,
                                                 planned_end_date=now + datetime.timedelta(days=5),
                                                 planned_budget=10.15,
                                                 actual_budget=0.25)  # A task for user 'test_user2'

    def test_create(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)

        # normal request
        response = self.client.post(self.url, data={
            "name": "name1df",
            "task": self.task1.id,
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2021-08-31T00:00",
            "actual_end_date": "2022-02-01T00:06",
            "actual_budget": 30,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {
            'id': 1,
            'name': 'name1df',
            'task': 1,
            'description': '',
            'planned_start_date': '2021-08-31T00:00:00Z',
            'planned_end_date': '2022-08-31T00:00:00Z',
            'planned_budget': '55.50',
            'actual_start_date': '2021-08-31T00:00:00Z',
            'actual_end_date': '2022-02-01T00:06:00Z',
            'actual_budget': '30.00',
            'dependency': None,
            'state': None,
            'assignees': []
        })
        self.assertEqual(response.data, ActivitySerializer(Activity.objects.get(id=1)).data)

    def test_without_task(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, data={
            "name": "name1df",
            # "task": self.task1.id,
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2021-08-31T00:00",
            "actual_end_date": "2022-02-01T00:06",
            "actual_budget": 30,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'task': ['This field is required.']})

    def test_with_team_member(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, data={
            "name": "name1df",
            "task": self.task_u1.id,
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2021-08-31T00:00",
            "actual_end_date": "2022-02-01T00:06",
            "actual_budget": 30,
        })
        self.assertEqual(response.status_code, 201, "he is team_member of 'team_for_username1'")

    def test_with_others_task(self):
        self.client.force_login(self.test_user2)

        response = self.client.post(self.url, data={
            "name": "name1df",
            "task": self.task_u1.id,
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2021-08-31T00:00",
            "actual_end_date": "2022-02-01T00:06",
            "actual_budget": 30,
        })
        self.assertEqual(response.status_code, 400, "he isn't project_manager neither team_member of project1")
        self.assertEqual(response.data, {'task': [f'Invalid pk "{self.task_u1.id}" - object does not exist.']})

        response = self.client.post(self.url, data={
            "name": "name1df",
            "task": 6544,
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2021-08-31T00:00",
            "actual_end_date": "2022-02-01T00:06",
            "actual_budget": 30,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'task': ['Invalid pk "6544" - object does not exist.']})

    def test_planned_end_date_before_planned_start_date(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, data={
            "task": self.task1.id,
            "name": "name1",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2021-08-30T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2021-08-31T00:00",
            "actual_end_date": "2022-02-01T00:06",
            "actual_budget": 30,
            "description": "",
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'planned_end_date': ['planned_start_date should be before planned_end_date.']
        })

    def test_actual_start_or_end_date_after_now(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data={
            "task": self.task1.id,
            "name": "name1",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2021-08-31T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2030-01-01T00:00",
            "actual_end_date": "2030-01-01T00:00",
            "actual_budget": 30,
            "description": "",
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'actual_start_date': ['actual_start_date should be before now.'],
            'actual_end_date': ['actual_end_date should be before now.']
        })

    def test_actual_end_date_before_actual_start_data(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data={
            "task": self.task1.id,
            "name": "test_34",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2021-08-31T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2022-01-01T00:00",
            "actual_end_date": "2021-01-01T00:00",
            "actual_budget": 30,
            "description": "",
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'actual_end_date': ['actual_start_date should be before actual_end_date.']
        })

    def test_without_actual_start_or_end_date(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, data={
            "task": self.task1.id,
            "name": "name1",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "planned_budget": 55.5,
            # "actual_start_date": "2021-08-31T00:00",
            # "actual_end_date": "2022-02-01T00:06",
            "actual_budget": 30,
            "description": "",
        })
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data['actual_start_date'])
        self.assertIsNone(response.data['actual_end_date'])

    def test_without_budget(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, data={
            "task": self.task1.id,
            "name": "name3",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            # "planned_budget": '55.5',
            "actual_start_date": "2021-08-31T00:00",
            "actual_end_date": "2022-02-01T00:06",
            # "actual_budget": '30',
            "description": "",
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['planned_budget'], None)
        self.assertEqual(response.data['actual_budget'], None)

    def test_budget_in_quotation(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, data={
            "task": self.task1.id,
            "name": "name3",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "planned_budget": '55.5',
            "actual_start_date": "2021-08-31T00:00",
            "actual_end_date": "2022-02-01T00:06",
            "actual_budget": '30',
            "description": "",
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['planned_budget'], '55.50')
        self.assertEqual(response.data['actual_budget'], '30.00')

    def test_without_description(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, data={
            "task": self.task1.id,
            "name": "name1df",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2021-08-31T00:00",
            "actual_end_date": "2022-02-01T00:06",
            "actual_budget": 30,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["description"], "")

    def test_with_state(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, data={
            "task": self.task1.id,
            "name": "name1df",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "state": self.state1.id
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["state"], self.state1.id)

    def test_with_state_my_project2(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, data={
            "task": self.task1.id,
            "name": "name1df",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "state": self.state3.id
        })
        self.assertEqual(response.status_code, 400, 'state3 is for project2 and task1 for project1')
        self.assertEqual(response.data, {
            'non_field_errors': ['projects not match.']
        })

    def test_with_others_state(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, data={
            "task": self.task1.id,
            "name": "name1df",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "state": self.state_for_test_user2.id
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'state': [f'Invalid pk "{self.state_for_test_user2.id}" - object does not exist.']
        })

        response = self.client.post(self.url, data={
            "task": self.task1.id,
            "name": "name1df",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "state": 54654
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'state': ['Invalid pk "54654" - object does not exist.']
        })

    def test_with_dependency(self):
        self.client.force_login(self.user)

        activity1_id = self.client.post(self.url, data={
            "task": self.task1.id,
            "name": "activity1",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
        }).data['id']

        response = self.client.post(self.url, data={
            "task": self.task1.id,
            "name": "name1df",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "dependency": activity1_id
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["dependency"], activity1_id)

    def test_with_other_task_dependency(self):
        self.client.force_login(self.user)

        activity1_id = self.client.post(self.url, data={
            "task": self.task1.id,
            "name": "activity1",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
        }).data['id']

        response = self.client.post(self.url, data={
            "task": self.task2.id,
            "name": "name1df",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "dependency": activity1_id
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["dependency"], activity1_id)

    def test_with_other_project_dependency(self):
        self.client.force_login(self.user)

        activity1_id = self.client.post(self.url, data={
            "task": self.task3.id,  # task3 is for project 2
            "name": "activity1",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
        }).data['id']

        response = self.client.post(self.url, data={
            "task": self.task1.id,  # its for project 1
            "name": "name1df",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "dependency": activity1_id
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'non_field_errors': ['projects not match.']
        })

    def test_with_others_dependency(self):
        self.client.force_login(self.test_user2)

        activity1_id = self.client.post(self.url, data={
            "task": self.task_test_user.id,  # it's for test_ussr2
            "name": "activity1",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
        }).data['id']

        self.client.force_login(self.username1)

        response = self.client.post(self.url, data={
            "task": self.task1.id,  # its for project 1
            "name": "name1df",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "dependency": activity1_id
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'dependency': [f'Invalid pk "{activity1_id}" - object does not exist.']
        })


class TestActivity(GanttMixin, APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse('gantt:activity-list')

        cls.test_user2 = _create_user('t2')
        cls.just_authenticated = _create_user('just')

        # create projects
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        cls.project1 = Project.objects.create(name='First Project', planned_start_date=now, planned_end_date=now,
                                              actual_start_date=now, actual_end_date=now, project_manager=cls.user)
        cls.project2 = Project.objects.create(name='Second Project', planned_start_date=now, planned_end_date=now,
                                              actual_start_date=now, actual_end_date=now, project_manager=cls.user)
        cls.project_for_usrname1 = Project.objects.create(name='Project for username1', planned_start_date=now,
                                                          planned_end_date=now, actual_start_date=now,
                                                          actual_end_date=now, project_manager=cls.username1)
        cls.project_for_test_user2 = Project.objects.create(name='nothing', planned_start_date=now,
                                                            planned_end_date=now,
                                                            actual_start_date=now, actual_end_date=now,
                                                            project_manager=cls.test_user2)

        # create teams
        cls.team1 = Team.objects.create(name='First Team', project=cls.project1)
        cls.team2 = Team.objects.create(name='Second Team', project=cls.project1)
        cls.team3 = Team.objects.create(name='3rd Team for project2', project=cls.project2)
        cls.team_for_username1 = Team.objects.create(name='Team for username1 project',
                                                     project=cls.project_for_usrname1)

        # create roles
        cls.role1 = Role.objects.create(name='First role', project=cls.project1)
        cls.role2 = Role.objects.create(name='Second role', project=cls.project1)
        cls.role3 = Role.objects.create(name='3rd role', project=cls.project2)
        cls.role_for_username1 = Role.objects.create(name='4th role', project=cls.project_for_usrname1)

        # create team-members
        cls.member1 = TeamMember.objects.create(team=cls.team1, user=cls.username1, role=cls.role1)
        cls.member2 = TeamMember.objects.create(team=cls.team2, user=cls.username1, role=cls.role1)
        cls.member3 = TeamMember.objects.create(team=cls.team3, user=cls.username1, role=cls.role3)
        cls.member_u1 = TeamMember.objects.create(team=cls.team_for_username1, user=cls.user,
                                                  role=cls.role_for_username1)
        cls.test_user2_member = TeamMember.objects.create(team=cls.team1, user=cls.test_user2, role=cls.role1)

        # create states
        cls.state1 = State.objects.create(name='state1', project=cls.project1)
        cls.state2 = State.objects.create(name='state2', project=cls.project1)
        cls.state3 = State.objects.create(name='state3', project=cls.project2)
        cls.state_for_username1 = State.objects.create(name='s for u1', project=cls.project_for_usrname1)
        cls.state_for_test_user2 = State.objects.create(name='s for test u2', project=cls.project_for_test_user2)

        # create tasks
        cls.task1 = Task.objects.create(name='task1', project=cls.project1, planned_start_date=now,
                                        planned_end_date=now + datetime.timedelta(days=2),
                                        planned_budget=1, actual_budget=4)

        cls.task2 = Task.objects.create(name='task2', project=cls.project1, planned_start_date=now,
                                        planned_end_date=now + datetime.timedelta(days=2),
                                        planned_budget=0, actual_start_date=now - datetime.timedelta(hours=1),
                                        actual_end_date=now, actual_budget=4)

        cls.task3 = Task.objects.create(name='task3', project=cls.project2, planned_start_date=now,
                                        planned_end_date=now + datetime.timedelta(weeks=4), planned_budget=11.5,
                                        actual_start_date=now, actual_budget=0.6)

        cls.task_u1 = Task.objects.create(name='task_u1', project=cls.project_for_usrname1, planned_start_date=now,
                                          planned_end_date=now + datetime.timedelta(days=5), planned_budget=10.15,
                                          actual_budget=0.25)  # A task for the user 'username1'

        cls.task_test_user = Task.objects.create(name='task_test_u', project=cls.project_for_test_user2,
                                                 planned_start_date=now,
                                                 planned_end_date=now + datetime.timedelta(days=5),
                                                 planned_budget=10.15,
                                                 actual_budget=0.25)  # A task for user 'test_user2'

    def setUp(self):
        now = datetime.datetime.now(tz=datetime.timezone.utc)

        # create activities
        self.activity1 = Activity.objects.create(name='ac1', task=self.task1, planned_start_date=now,
                                                 planned_end_date=now + datetime.timedelta(days=5))

        self.activity2 = Activity.objects.create(name='ac2', task=self.task1, planned_start_date=now,
                                                 planned_end_date=now + datetime.timedelta(hours=20))

        self.activity3 = Activity.objects.create(name='ac3', task=self.task2, planned_start_date=now,
                                                 planned_end_date=now + datetime.timedelta(days=53))

        self.activity_for_project2 = Activity.objects.create(name='ac p2', task=self.task3, planned_start_date=now,
                                                             planned_end_date=now + datetime.timedelta(days=56))

        self.activity_u1 = Activity.objects.create(name='ac u1', task=self.task_u1, planned_start_date=now,
                                                   planned_end_date=now + datetime.timedelta(days=25))

        self.activity_test_user = Activity.objects.create(name='ac tu2', task=self.task_test_user, planned_start_date=now,
                                                          planned_end_date=now + datetime.timedelta(days=17))

    def test_get(self):
        url = reverse('gantt:activity-detail', kwargs={'pk': self.activity1.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, ActivitySerializer(self.activity1).data)

        url = reverse('gantt:activity-detail', kwargs={'pk': self.activity_u1.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, "he is employee of the task's project.")
        self.assertEqual(response.data, ActivitySerializer(self.activity_u1).data)

        url = reverse('gantt:activity-detail', kwargs={'pk': self.activity_test_user.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404, "he is not employee nor project_manager of activity__task_project")
        self.assertEqual(response.data, {'detail': 'Not found.'})

    def test_put(self):
        url = reverse('gantt:activity-detail', kwargs={'pk': self.activity1.id})
        self.client.force_login(self.user)

        response = self.client.put(url, data={
            "id": self.activity1.id,
            "task": self.activity3.task.id,
            "name": self.activity1.name,
            "planned_start_date": "2021-08-31T00:00:00Z",
            "planned_end_date": "2022-08-31T00:00:00Z",
            "planned_budget": "55.50",
            "actual_start_date": "2021-08-31T00:00:00Z",
            "actual_end_date": "2022-02-01T00:06:00Z",
            "actual_budget": "30.00",
            "description": "description."
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['task'], self.activity3.task_id)
        self.activity1.refresh_from_db()
        self.assertEqual(response.data, ActivitySerializer(self.activity1).data)

        response = self.client.put(url, format='json', data={
            "name": self.activity1.name,
            "planned_start_date": "2021-08-31T00:00:00Z",
            "planned_end_date": "2022-08-31T00:00:00Z",
            "actual_start_date": None
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['actual_start_date'], None)

    def test_patch(self):
        url = reverse('gantt:activity-detail', kwargs={'pk': self.activity1.id})
        self.client.force_login(self.user)

        response = self.client.patch(url, data={
            "name": 'hello',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'hello')
        self.activity1.refresh_from_db()
        self.assertEqual(response.data, ActivitySerializer(self.activity1).data)

    def test_change_date(self):
        url = reverse('gantt:activity-detail', kwargs={'pk': self.activity1.id})
        self.client.force_login(self.user)

        now = datetime.datetime.now()

        response = self.client.patch(url, data={
            'planned_start_date': now + datetime.timedelta(days=50)
        })
        self.assertEqual(response.status_code, 400, 'planned_start_date should be before planned_end_date.')

        response = self.client.patch(url, data={
            'planned_start_date': now + datetime.timedelta(seconds=1),
            'planned_end_date': now
        })
        self.assertEqual(response.status_code, 400, 'planned_start_date should be before planned_end_date.')

        response = self.client.patch(url, data={
            'actual_start_date': now + datetime.timedelta(seconds=1),
        })
        self.assertEqual(response.status_code, 400, 'actual_start_date should be before now.')

        response = self.client.patch(url, data={
            'actual_start_date': now,
        })
        self.assertEqual(response.status_code, 200)

        response = self.client.patch(url, data={
            'actual_end_date': now - datetime.timedelta(seconds=1),
        })
        self.assertEqual(response.status_code, 400, 'actual_start_date should be before actual_end_date.')

        response = self.client.patch(url, data={
            'actual_end_date': now,
        })
        self.assertEqual(response.status_code, 200)

        response = self.client.patch(url, data={
            'actual_start_date': now + datetime.timedelta(weeks=1),
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(response.data.items()), 2, 'should returns 2 errors.')

    def test_change_state(self):
        url = reverse('gantt:activity-detail', kwargs={'pk': self.activity1.id})
        self.client.force_login(self.user)

        response = self.client.patch(url, data={
            'state': ''
        })
        self.assertEqual(response.status_code, 200)

        response = self.client.patch(url, data={
            'state': self.state1.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['state'], self.state1.id)

        response = self.client.patch(url, data={
            'state': self.state3.id  # it's for project2
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'non_field_errors': ['projects not match.']})

        response = self.client.patch(url, data={
            'state': self.state_for_test_user2.id  # it's for testuser2
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'state': [f'Invalid pk "{self.state_for_test_user2.id}" - object does not exist.']
        })

        response = self.client.patch(url, data={
            'state': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['state'], None)

    def test_change_dependency(self):
        url = reverse('gantt:activity-detail', kwargs={'pk': self.activity1.id})
        self.client.force_login(self.user)

        response = self.client.patch(url, data={
            'dependency': ''
        })
        self.assertEqual(response.status_code, 200)

        response = self.client.patch(url, data={
            'dependency': self.activity1.id
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'dependency': [f'Invalid pk "{self.activity1.id}" - object does not exist.']
        })

        response = self.client.patch(url, data={
            'dependency': self.activity2.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['dependency'], self.activity2.id)

        response = self.client.patch(url, data={
            'dependency': self.activity_for_project2.id
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'non_field_errors': ['projects not match.']})

        response = self.client.patch(url, data={
            'dependency': self.activity_test_user.id
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'dependency': [f'Invalid pk "{self.activity_test_user.id}" - object does not exist.']
        })

    def test_delete(self):
        url = reverse('gantt:activity-detail', kwargs={'pk': self.activity1.id})
        self.client.force_login(self.user)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Activity.objects.filter(id=self.activity1.id).exists())

        url = reverse('gantt:activity-detail', kwargs={'pk': self.activity_u1.id})  # he is employee of its project.

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Activity.objects.filter(id=self.activity_u1.id).exists())

        url = reverse('gantt:activity-detail', kwargs={'pk': self.activity_test_user.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404, 'he is not employee or project_manager of its project.')
        self.assertTrue(Activity.objects.filter(id=self.activity_test_user.id).exists())


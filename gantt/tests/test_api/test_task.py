import datetime

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from gantt.models import Task, Role, Team, TeamMember, Project
from gantt.tests.base import GanttMixin, _create_user

now = datetime.datetime.now(tz=datetime.timezone.utc)


class TestTaskCreate(GanttMixin, APITestCase):

    def setUp(self) -> None:
        self.url = reverse('gantt:task-list')

        self.client.force_login(self.user)
        project_url = reverse('gantt:project-list')

        # creating projects for the main user
        project1 = self.client.post(project_url, data={
            "name": "first",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2021-09-10",
            "actual_start_date": "2021-09-01",
            "actual_end_date": "2021-09-02",
        })
        assert project1.status_code == 201
        self.project1_id = project1.data['id']

        project2 = self.client.post(project_url, data={
            "name": "2nd",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2021-09-10",
            "actual_start_date": "2021-09-01",
            "actual_end_date": "2021-09-02",
        })
        assert project2.status_code == 201
        self.project2_id = project2.data['id']

        self.client.logout()
        self.client.force_login(self.username1)

        other_project = self.client.post(project_url, data={
            "name": "project for username1",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2022-09-10",
            "actual_start_date": "2021-09-01",
            "actual_end_date": "2022-09-02",
        })
        assert other_project.status_code == 201
        self.project_id_for_username1 = other_project.data['id']

        self.client.logout()

    def test_create(self):
        url = self.url

        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)

        # normal request
        response = self.client.post(url, data={
            "project": self.project1_id,
            "name": "name1",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2021-08-31T00:00",
            "actual_end_date": "2022-02-01T00:06",
            "actual_budget": 30,
            "description": "",
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(type(response.data.get('id')) is int)
        self.assertEqual(response.data, {
            "id": response.data.get('id'),
            "project": self.project1_id,
            "name": "name1",
            "planned_start_date": "2021-08-31T00:00:00Z",
            "planned_end_date": "2022-08-31T00:00:00Z",
            "planned_budget": "55.50",
            "actual_start_date": "2021-08-31T00:00:00Z",
            "actual_end_date": "2022-02-01T00:06:00Z",
            "actual_budget": "30.00",
            "description": "",
        })

    def test_without_project(self):
        url = self.url
        self.client.force_login(self.user)

        response = self.client.post(url, data={
            "name": "without project",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2021-08-31T00:00",
            "actual_end_date": "2022-02-01T00:06",
            "actual_budget": 30,
            "description": "",
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            "project": [
                "This field is required."
            ]
        })

        # with null project
        response = self.client.post(url, data={
            "project": '',
            "name": "without project",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2021-08-31T00:00",
            "actual_end_date": "2022-02-01T00:06",
            "actual_budget": 30,
            "description": "",
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            "project": [
                "This field may not be null."
            ]
        })

    def test_with_others_project(self):
        url = self.url
        self.client.force_login(self.user)

        response = self.client.post(url, data={
            "project": self.project_id_for_username1,
            "name": "without project",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2021-08-31T00:00",
            "actual_end_date": "2022-02-01T00:06",
            "actual_budget": 30,
            "description": "",
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            "project": [
                f'Invalid pk "{self.project_id_for_username1}" - object does not exist.'
            ]
        })

        response = self.client.post(url, data={
            "project": 257,
            "name": "without project",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2021-08-31T00:00",
            "actual_end_date": "2022-02-01T00:06",
            "actual_budget": 30,
            "description": "",
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            "project": [
                f'Invalid pk "257" - object does not exist.'
            ]
        })

    def test_duplicate_tasks_with_same_attributes(self):
        url = self.url
        self.client.force_login(self.user)

        response = self.client.post(url, data={
            "project": self.project1_id,
            "name": "name1",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2021-08-31T00:00",
            "actual_end_date": "2022-02-01T00:06",
            "actual_budget": 30,
            "description": "",
        })
        self.assertEqual(response.status_code, 201)
        task1_id = response.data.get('id')
        self.assertEqual(response.data, {
            "id": task1_id,
            "project": self.project1_id,
            "name": "name1",
            "planned_start_date": "2021-08-31T00:00:00Z",
            "planned_end_date": "2022-08-31T00:00:00Z",
            "planned_budget": "55.50",
            "actual_start_date": "2021-08-31T00:00:00Z",
            "actual_end_date": "2022-02-01T00:06:00Z",
            "actual_budget": "30.00",
            "description": "",
        })

        response = self.client.post(url, data={
            "project": self.project1_id,
            "name": "name1",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2021-08-31T00:00",
            "actual_end_date": "2022-02-01T00:06",
            "actual_budget": 30,
            "description": "",
        })
        self.assertEqual(response.status_code, 201)
        task2_id = response.data.get('id')
        self.assertEqual(response.data, {
            "id": task2_id,
            "project": self.project1_id,
            "name": "name1",
            "planned_start_date": "2021-08-31T00:00:00Z",
            "planned_end_date": "2022-08-31T00:00:00Z",
            "planned_budget": "55.50",
            "actual_start_date": "2021-08-31T00:00:00Z",
            "actual_end_date": "2022-02-01T00:06:00Z",
            "actual_budget": "30.00",
            "description": "",
        })
        self.assertNotEqual(task1_id, task2_id)
        self.assertIsNotNone(task2_id)
        self.assertIsNotNone(task1_id)

    def test_create_without_priority(self):
        url = self.url
        self.client.force_login(self.user)

        response = self.client.post(url, data={
            "project": self.project1_id,
            "name": "name2",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2021-08-31T00:00",
            "actual_end_date": "2022-02-01T00:06",
            "actual_budget": 30,
            "description": "",
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {
            "id": response.data.get('id'),
            "project": self.project1_id,
            "name": "name2",
            "planned_start_date": "2021-08-31T00:00:00Z",
            "planned_end_date": "2022-08-31T00:00:00Z",
            "planned_budget": '55.50',
            "actual_start_date": "2021-08-31T00:00:00Z",
            "actual_end_date": "2022-02-01T00:06:00Z",
            "actual_budget": '30.00',
            "description": "",
        })

    def test_planned_end_date_before_planned_start_date(self):
        url = self.url
        self.client.force_login(self.user)

        response = self.client.post(url, data={
            "project": self.project1_id,
            "name": "name1",
            "priority": 0,
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2021-08-30T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2021-08-31T00:00",
            "actual_end_date": "2022-02-01T00:06",
            "actual_budget": 30,
            "description": "",
            "rank": "12"
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'planned_end_date': ['planned_start_date should be before planned_end_date.']
        })

    def test_actual_start_or_end_date_after_now(self):
        url = self.url
        self.client.force_login(self.user)
        response = self.client.post(url, data={
            "project": self.project1_id,
            "name": "name1",
            "priority": 0,
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2021-08-31T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2030-01-01T00:00",
            "actual_end_date": "2030-01-01T00:00",
            "actual_budget": 30,
            "description": "",
            "rank": "12"
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'actual_start_date': ['actual_start_date should be before now.'],
            'actual_end_date': ['actual_end_date should be before now.']
        })

    def test_actual_end_date_before_actual_start_data(self):
        url = self.url
        self.client.force_login(self.user)
        response = self.client.post(url, data={
            "project": self.project1_id,
            "name": "test_34",
            "priority": 0,
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2021-08-31T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2022-01-01T00:00",
            "actual_end_date": "2021-01-01T00:00",
            "actual_budget": 30,
            "description": "",
            "rank": "12"
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'actual_end_date': ['actual_start_date should be before actual_end_date.']
        })

    def test_without_actual_start_or_end_date(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, data={
            "project": self.project1_id,
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
        self.assertEqual(response.data, {
            "id": response.data.get('id'),
            "project": self.project1_id,
            "name": "name1",
            "planned_start_date": "2021-08-31T00:00:00Z",
            "planned_end_date": "2022-08-31T00:00:00Z",
            "planned_budget": "55.50",
            "actual_start_date": None,
            "actual_end_date": None,
            "actual_budget": "30.00",
            "description": "",
        })

    def test_budget_in_quotation(self):
        url = self.url
        self.client.force_login(self.user)

        response = self.client.post(url, data={
            "project": self.project1_id,
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
        self.assertEqual(response.data, {
            "id": response.data.get('id'),
            "project": self.project1_id,
            "name": "name3",
            "planned_start_date": "2021-08-31T00:00:00Z",
            "planned_end_date": "2022-08-31T00:00:00Z",
            "planned_budget": '55.50',
            "actual_start_date": "2021-08-31T00:00:00Z",
            "actual_end_date": "2022-02-01T00:06:00Z",
            "actual_budget": '30.00',
            "description": "",
        })

    def test_without_description(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, data={
            "project": self.project1_id,
            "name": "name1df",
            "planned_start_date": "2021-08-31T00:00",
            "planned_end_date": "2022-08-31T00:00",
            "planned_budget": 55.5,
            "actual_start_date": "2021-08-31T00:00",
            "actual_end_date": "2022-02-01T00:06",
            "actual_budget": 30,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {
            "id": response.data.get('id'),
            "project": self.project1_id,
            "name": "name1df",
            "planned_start_date": "2021-08-31T00:00:00Z",
            "planned_end_date": "2022-08-31T00:00:00Z",
            "planned_budget": "55.50",
            "actual_start_date": "2021-08-31T00:00:00Z",
            "actual_end_date": "2022-02-01T00:06:00Z",
            "actual_budget": "30.00",
            "description": "",
        })

    # def test_without_rank(self):
    #     self.client.force_login(self.user)
    #
    #     response = self.client.post(self.url, data={
    #         "project": self.project1_id,
    #         "name": "name1df",
    #         "planned_start_date": "2021-08-31T00:00",
    #         "planned_end_date": "2022-08-31T00:00",
    #         "planned_budget": 55.5,
    #         "actual_start_date": "2021-08-31T00:00",
    #         "actual_end_date": "2022-02-01T00:06",
    #         "actual_budget": 30,
    #         "description": "description.",
    #     })
    #     self.assertEqual(response.status_code, 201)
    #     self.assertEqual(response.data, {
    #         "id": response.data.get('id'),
    #         "project": self.project1_id,
    #         "name": "name1df",
    #         "priority": 2,
    #         "planned_start_date": "2021-08-31T00:00:00Z",
    #         "planned_end_date": "2022-08-31T00:00:00Z",
    #         "planned_budget": "55.50",
    #         "actual_start_date": "2021-08-31T00:00:00Z",
    #         "actual_end_date": "2022-02-01T00:06:00Z",
    #         "actual_budget": "30.00",
    #         "description": "description.",
    #     })


class TestTask(GanttMixin, APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.test_user2 = _create_user('t2')
        cls.just_authenticated = _create_user('just')

        # create projects
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

    def setUp(self) -> None:
        # create tasks
        self.task1 = Task.objects.create(name='task1', project=self.project1, planned_start_date=now,
                                         planned_end_date=now + datetime.timedelta(days=2),
                                         planned_budget=1, actual_budget=4)

        self.task2 = Task.objects.create(name='task2', project=self.project1, planned_start_date=now,
                                         planned_end_date=now + datetime.timedelta(days=2),
                                         planned_budget=0, actual_start_date=now - datetime.timedelta(hours=1),
                                         actual_end_date=now, actual_budget=4)

        self.task3 = Task.objects.create(name='task3', project=self.project2, planned_start_date=now,
                                         planned_end_date=now + datetime.timedelta(weeks=4), planned_budget=11.5,
                                         actual_start_date=now, actual_budget=0.6)

        self.task_u1 = Task.objects.create(name='task_u1', project=self.project_for_usrname1, planned_start_date=now,
                                           planned_end_date=now + datetime.timedelta(days=5), planned_budget=10.15,
                                           actual_budget=0.25)  # A task for the user 'username1'

    def test_get_tasks_list_with_project_manager(self):
        """to test a project manager can see his tasks"""

        url = reverse('gantt:task-list', kwargs={'proj_pk': self.project1.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, msg='A project manager should get tasks of the project.')
        self.assertEqual(len(response.data), Task.objects.filter(project=self.project1).count())

        expected = [t[0] for t in Task.objects.filter(project=self.project1).values_list('name')]
        result = [t['name'] for t in response.data]
        self.assertEqual(result, expected)
        self.client.logout()

    def test_get_tasks_list_with_other_project_manager(self):
        """ to test other project managers can't see others tasks """

        url = reverse('gantt:task-list', kwargs={'proj_pk': self.project2.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.test_user2)
        # user 't2' is project manager of other project and his is not employee of 'project2'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [], msg='he is not employee nor project manager')
        self.client.logout()

    def test_get_tasks_list_with_employee(self):
        url = reverse('gantt:task-list', kwargs={'proj_pk': self.project1.id})
        # to test an employee can see its project's tasks
        self.client.force_login(self.username1)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, msg='An employee should get tasks of the project he works on.')
        self.assertEqual(len(response.data), Task.objects.filter(project=self.project1).count())

        expected = [t[0] for t in Task.objects.filter(project=self.project1).values_list('name')]
        result = [t['name'] for t in response.data]
        self.assertEqual(result, expected)
        self.client.logout()

    def test_get_tasks_list_with_other_employee(self):
        """to test other employee can't see other's project's tasks"""

        url = reverse('gantt:task-list', kwargs={'proj_pk': self.project2.id})
        self.client.force_login(self.test_user2)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
        self.client.logout()

    def test_get_tasks_list_with_unknown_user(self):
        url = reverse('gantt:task-list', kwargs={'proj_pk': self.project1.id})
        # to test authenticated unknown person can't see the project's tasks
        self.client.force_login(self.just_authenticated)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [], msg='testing with unknown user and existing project or '
                                                'testing with none-existing project, should return `[]` as response')
        self.client.logout()

    def test_get_tasks_list_with_none_existing_project(self):
        url = reverse('gantt:task-list', kwargs={'proj_pk': 6546432654})
        self.client.force_login(self.user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [], msg='testing with unknown user and existing project or '
                                                'testing with none-existing project, should return `[]` as response')

        self.client.logout()

    def test_other_methods_with_tasks_list(self):
        """ The view should only allow get method.
        """

        import json
        url = reverse('gantt:task-list', kwargs={'proj_pk': self.project1.id})
        self.client.force_login(self.user)

        data = json.dumps([{}])
        methods = ('POST', 'PUT', 'PATCH', 'DELETE')

        for method in methods:
            r = self.client.generic(method, url, data)
            self.assertEqual(r.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
            self.assertEqual(r.data, {'detail': f'Method "{method}" not allowed.'})

        self.client.logout()

    def test_get_task(self):
        task = self.task1
        url = reverse('gantt:task-detail', kwargs={'pk': task.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], task.id)
        self.assertEqual(response.data['name'], task.name)
        self.assertEqual(tuple(response.data.keys()),
                         ("id", "project", "name", "planned_start_date",
                          "planned_end_date", "planned_budget", "actual_start_date",
                          "actual_end_date", "actual_budget", "description"))

        url = reverse('gantt:task-detail', kwargs={'pk': self.task_u1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'self.user is employee of the project.')

        url = reverse('gantt:task-detail', kwargs={'pk': self.task3.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.client.logout()
        self.client.force_login(self.username1)

        url = reverse('gantt:task-detail', kwargs={'pk': self.task_u1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        url = reverse('gantt:task-detail', kwargs={'pk': self.task1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'username1 is employee of project.')

        self.client.logout()
        self.client.force_login(self.test_user2)

        url = reverse('gantt:task-detail', kwargs={'pk': self.task3.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404, 't2 is not employee or project manager of project.')
        self.client.logout()

    def test_post_single_task(self):
        url = reverse('gantt:task-detail', kwargs={'pk': self.task1.id})

        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.client.logout()

    def test_put_task(self):
        task = self.task1
        url = reverse('gantt:task-detail', kwargs={'pk': task.id})

        response = self.client.put(url)
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)

        data = {
            "id": task.id,
            "project": task.project.id,
            "name": task.name,
            "planned_start_date": "2021-08-31T00:00:00Z",
            "planned_end_date": "2022-08-31T00:00:00Z",
            "planned_budget": "55.50",
            "actual_start_date": "2021-08-31T00:00:00Z",
            "actual_end_date": "2022-02-01T00:06:00Z",
            "actual_budget": "30.00",
            "description": "description.",
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, data)

        data['project'] = self.task3.project.id
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, 200)
        self.task1.refresh_from_db()
        self.assertEqual(self.task1.project.id, task.project.id, 'it should ignore project from inputs.')

        del data['project']
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, 200)

        data['id'] = self.task2.id
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, 200)
        data['id'] = self.task1.id
        data['project'] = self.task1.project.id
        self.assertEqual(response.data, data)

        del data['id']
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, 200)

        self.client.logout()
        self.client.force_login(self.test_user2)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'he should read the task.')
        self.assertEqual(response.data['id'], task.id)
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, 403, "he can't change the task.")

        self.client.logout()

    def test_patch_task(self):
        task = self.task1
        url = reverse('gantt:task-detail', kwargs={'pk': task.id})

        response = self.client.patch(url)
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)

        data = {
            "id": task.id,
            "project": task.project.id,
            "name": task.name,
            "planned_start_date": "2021-08-31T00:00:00Z",
            "planned_end_date": "2022-08-31T00:00:00Z",
            "planned_budget": "55.50",
            "actual_start_date": "2021-08-31T00:00:00Z",
            "actual_end_date": "2022-02-01T00:06:00Z",
            "actual_budget": "30.00",
            "description": "description.",
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, data)

        # data['project'] = self.task3.project.id
        response = self.client.patch(url, data={
            'project': self.task3.project.id
        })
        self.assertEqual(response.status_code, 200)
        self.task1.refresh_from_db()
        self.assertEqual(self.task1.project.id, task.project.id, 'it should ignore project from inputs.')

        response = self.client.patch(url, data={
            'name': 'task1 (new)'
        })
        self.assertEqual(response.status_code, 200)
        self.task1.refresh_from_db()
        self.assertEqual(response.data['name'], self.task1.name)
        data['name'] = self.task1.name
        self.assertEqual(response.data, data)

        response = self.client.patch(url, data={
            'id': 45
        })
        self.assertEqual(response.data['id'], task.id)

        self.client.logout()
        self.client.force_login(self.test_user2)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'he should read the task.')
        self.assertEqual(response.data['id'], task.id)

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 403, "he can't change the task.")

        response = self.client.patch(url, data={
            'name': 'chert'
        })
        self.assertEqual(response.status_code, 403, "he can't change name of the task.")

        response = self.client.patch(url, data={
            'project': self.project_for_test_user2.id
        })
        self.assertEqual(response.status_code, 403, "he can't change the task.")
        self.task1.refresh_from_db()
        self.assertNotEqual(self.task1.project.id, self.project_for_test_user2.id)

        self.client.logout()

    def test_delete_task(self):
        url = reverse('gantt:task-detail', kwargs={'pk': self.task1.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 401)
        self.assertTrue(Task.objects.filter(id=self.task1.id).exists())

        self.client.force_login(self.test_user2)

        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Task.objects.filter(id=self.task1.id).exists())

        self.client.logout()
        self.client.force_login(self.user)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=self.task1.id).exists())

        self.client.logout()

    def test_change_date(self):
        # keys = ("planned_start_date", "planned_end_date", "actual_start_date", "actual_end_date")
        # dates = lambda d: {k: v for k, v in d.items() if k in keys}

        url = reverse('gantt:task-detail', kwargs={'pk': self.task1.id})
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

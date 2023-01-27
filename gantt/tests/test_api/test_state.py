import datetime

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from gantt.models import Project, State, Team, Role, TeamMember
from gantt.serializers import StateSerializer
from gantt.tests.base import GanttMixin


class TestStateCreate(GanttMixin, APITestCase):
    def setUp(self):
        self.url = reverse('gantt:state-list')

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

    def test_without_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create(self):
        self.client.force_login(self.user)

        # normal request
        response = self.client.post(self.url, {
            "name": "state1",
            "project": self.project1_id
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {
            "id": 1,
            "name": "state1",
            "project": self.project1_id
        })
        self.assertEqual(State.objects.count(), 1)

    def test_without_project(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, {
            "name": "state1",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            'project': ['This field is required.']
        })

        response = self.client.post(self.url, data={
            "name": "state1",
            "project": ''
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            'project': ['This field may not be null.']
        })

        self.assertEqual(State.objects.count(), 0)

    def test_create_with_others_project(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, {
            "name": "state1",
            "project": self.project_id_for_username1
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            "project": [
                f'Invalid pk "{self.project_id_for_username1}" - object does not exist.'
            ]
        })

        response = self.client.post(self.url, {
            "name": "state1",
            "project": 6544
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            "project": [
                f'Invalid pk "{6544}" - object does not exist.'
            ]
        })

    def test_with_duplicate_attributes(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, {
            "name": "state1",
            "project": self.project1_id
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {
            "id": 1,
            "name": "state1",
            "project": self.project1_id
        })

        response = self.client.post(self.url, {
            "name": "state1",
            "project": self.project1_id
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {
            "id": 2,
            "name": "state1",
            "project": self.project1_id
        })

        self.assertEqual(State.objects.count(), 2)


class TestState(GanttMixin, APITestCase):
    def setUp(self):
        # create projects
        now = datetime.datetime.now()
        self.project1 = Project.objects.create(name='First Project', planned_start_date=now, planned_end_date=now,
                                               actual_start_date=now, actual_end_date=now, project_manager=self.user)
        self.project2 = Project.objects.create(name='Second Project', planned_start_date=now, planned_end_date=now,
                                               actual_start_date=now, actual_end_date=now, project_manager=self.user)
        self.project_for_usrname1 = Project.objects.create(name='Project for username1', planned_start_date=now,
                                                           planned_end_date=now, actual_start_date=now,
                                                           actual_end_date=now, project_manager=self.username1)

        # create teams
        self.team1 = Team.objects.create(name='First Team', project=self.project1)
        self.team2 = Team.objects.create(name='Second Team', project=self.project1)
        self.team3 = Team.objects.create(name='3rd Team for project2', project=self.project2)
        self.team_for_username1 = Team.objects.create(name='Team for username1 project',
                                                      project=self.project_for_usrname1)
        self.team_for_user = Team.objects.create(name='name', project=self.project2)

        # create roles
        self.role1 = Role.objects.create(name='First role', project=self.project1)
        self.role2 = Role.objects.create(name='Second role', project=self.project1)
        self.role3 = Role.objects.create(name='3rd role', project=self.project2)
        self.role_for_username1 = Role.objects.create(name='4th role', project=self.project_for_usrname1)

        # create team-members
        self.member1 = TeamMember.objects.create(team=self.team1, user=self.username1, role=self.role1)
        self.member2 = TeamMember.objects.create(team=self.team2, user=self.username1, role=self.role1)
        self.member3 = TeamMember.objects.create(team=self.team3, user=self.username1, role=self.role3)
        self.member_u1 = TeamMember.objects.create(team=self.team_for_username1, user=self.user,
                                                   role=self.role_for_username1)
        # create states
        self.state1 = State.objects.create(name='state1', project=self.project1)
        self.state2 = State.objects.create(name='state2', project=self.project1)
        self.state3 = State.objects.create(name='state3', project=self.project2)
        self.state_for_username1 = State.objects.create(name='s for u1', project=self.project_for_usrname1)

    def test_get(self):
        url = reverse('gantt:state-detail', kwargs={'pk': self.state1.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, StateSerializer(self.state1).data, "he is project manager of state's project")

        url = reverse('gantt:state-detail', kwargs={'pk': self.state2.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, StateSerializer(self.state2).data, "he is project manager of state's project")

        url = reverse('gantt:state-detail', kwargs={'pk': self.state3.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, StateSerializer(self.state3).data, "he is project manager of state's project")

        url = reverse('gantt:state-detail', kwargs={'pk': self.state_for_username1.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, StateSerializer(self.state_for_username1).data, "he is team_member of state's project")

        self.client.force_login(self.username2)

        url = reverse('gantt:state-detail', kwargs={'pk': self.state1.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_put(self):
        self.client.force_login(self.user)

        url = reverse('gantt:state-detail', kwargs={'pk': self.state1.id})

        # normal request
        response = self.client.put(url, data={
            'name': self.state1.name
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, StateSerializer(self.state1).data)

        response = self.client.put(url, data={
            'name': self.state1.name,
            'project': 4565
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, StateSerializer(self.state1).data, 'should ignore project.')

        url = reverse('gantt:state-detail', kwargs={'pk': self.state_for_username1.id})

        response = self.client.put(url, data={
            'name': self.state1.name
        })
        self.assertEqual(response.status_code, 403, "he can't change it.")
        self.assertEqual(self.client.get(url).status_code, 200, 'he can get it.')
        self.assertEqual(response.data, {
            'detail': 'You do not have permission to perform this action.'
        })

    def test_patch(self):
        self.client.force_login(self.user)

        url = reverse('gantt:state-detail', kwargs={'pk': self.state1.id})

        # normal request
        response = self.client.patch(url, data={
            'name': self.state1.name
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, StateSerializer(self.state1).data)

        response = self.client.patch(url, data={
            'name': self.state1.name,
            'project': 4565
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, StateSerializer(self.state1).data, 'should ignore project.')

        url = reverse('gantt:state-detail', kwargs={'pk': self.state_for_username1.id})

        response = self.client.patch(url, data={
            'name': self.state1.name
        })
        self.assertEqual(response.status_code, 403, "he can't change it.")
        self.assertEqual(self.client.get(url).status_code, 200, 'he can get it.')
        self.assertEqual(response.data, {
            'detail': 'You do not have permission to perform this action.'
        })

    def test_delete(self):
        url = reverse('gantt:state-detail', kwargs={'pk': self.state1.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data, {
            'detail': 'Authentication credentials were not provided.'
        })
        self.assertTrue(State.objects.filter(id=self.state1.id).exists())

        self.client.force_login(self.user)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(State.objects.filter(id=self.state1.id).exists())

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

        url = reverse('gantt:state-detail', kwargs={'pk': self.state_for_username1.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403, "he can't change it.")
        self.assertEqual(self.client.get(url).status_code, 200, 'he can get it.')
        self.assertEqual(response.data, {
            'detail': 'You do not have permission to perform this action.'
        })
import datetime

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from gantt.models import Team, Project
from gantt.tests.base import GanttMixin


class TestCreateTeam(GanttMixin, APITestCase):
    def setUp(self) -> None:
        self.client.force_login(self.user)
        project_url = reverse('gantt:project-list')

        stat = self.client.post(project_url, data={
            "name": "first",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2021-09-10",
            "actual_start_date": "2021-09-01",
            "actual_end_date": "2021-09-02",
        }).status_code
        assert stat == 201
        stat = self.client.post(project_url, data={
            "name": "2nd",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2021-09-10",
            "actual_start_date": "2021-09-01",
            "actual_end_date": "2021-09-02",
        }).status_code
        assert stat == 201

        self.client.logout()

        now = datetime.datetime.now()
        Project.objects.create(name='df', actual_start_date=now, actual_end_date=now,
                               planned_start_date=now, planned_end_date=now, project_manager=self.username1)
        self.team_list = reverse('gantt:team-list')

    def test_without_login(self):
        msg = f'Request on "{self.team_list}" without credentials must return 403 status code.'
        response = self.client.get(self.team_list)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, msg)

        response = self.client.head(self.team_list)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, msg)

        response = self.client.post(self.team_list)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, msg)

        response = self.client.put(self.team_list)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, msg)

        response = self.client.patch(self.team_list)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, msg)

        response = self.client.options(self.team_list)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, msg)

        response = self.client.trace(self.team_list)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, msg)

        response = self.client.delete(self.team_list)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, msg)

        url = reverse('gantt:project-detail', kwargs={'pk': 1})

        msg = f'Request on "{url}" without credentials must return 403 status code.'

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, msg)

        response = self.client.head(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, msg)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, msg)

        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, msg)

        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, msg)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, msg)

        response = self.client.trace(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, msg)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, msg)

    def test_create_team(self):
        self.client.force_login(self.user)

        response = self.client.post(self.team_list, data={
            "name": "First Team",
            "project": 1
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {
            'id': 1,
            "name": "First Team",
            "project": 1
        })

        response = self.client.post(self.team_list, data={
            "name": "Second Team",
            "project": 1
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {
            'id': 2,
            "name": "Second Team",
            "project": 1
        })

        response = self.client.post(self.team_list, data={
            "name": "Frontend Team",
            "project": 2
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {
            'id': 3,
            "name": "Frontend Team",
            "project": 2
        })

        response = self.client.post(self.team_list, data={
            "name": "First Team",
            "project": 3
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            "project": [
                "Invalid pk \"3\" - object does not exist."
            ]
        })

        self.client.login()
        self.client.force_login(self.username1)

        response = self.client.post(self.team_list, data={
            'name': 'test',
            'project': 2
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            "project": [
                "Invalid pk \"2\" - object does not exist."
            ]
        })


class TestTeamGet(GanttMixin, APITestCase):
    def setUp(self) -> None:
        self.client.force_login(self.user)
        project_url = reverse('gantt:project-list')

        stat = self.client.post(project_url, data={
            "name": "first",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2021-09-10",
            "actual_start_date": "2021-09-01",
            "actual_end_date": "2021-09-02",
        }).status_code
        assert stat == 201
        stat = self.client.post(project_url, data={
            "name": "2nd",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2021-09-10",
            "actual_start_date": "2021-09-01",
            "actual_end_date": "2021-09-02",
        }).status_code
        assert stat == 201

        url = reverse('gantt:team-list')
        id_1 = self.client.post(url, {
            'name': 'first-team',
            'project': 1
        }).data['id']
        assert id_1 == 1

        id_2 = self.client.post(url, {
            'name': 'test',
            'project': 1
        }).data['id']
        assert id_2 == 2

        self.client.post(url, {
            'name': 'amir',
            'project': 1
        })

        self.client.logout()

        self.team_1 = reverse('gantt:team-detail', kwargs={'pk': id_1})
        self.team_2 = reverse('gantt:team-detail', kwargs={'pk': id_2})

        # create a team object for 'username1'
        self.client.force_login(self.username1)

        u1_project_id = self.client.post(project_url, data={
            "name": "username1`s Project",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2021-09-10",
            "actual_start_date": "2021-09-01",
            "actual_end_date": "2021-09-02",
            "description": "this is for `username1`."
        }).data['id']
        assert u1_project_id == 3

        url = reverse('gantt:team-list')
        id_u1 = self.client.post(url, {
            'name': 'A Team for Username1',
            'project': 3
        }).data['id']
        assert id_u1 == 4
        self.team_id_for_username1 = id_u1

        self.client.logout()

    def test_get_team(self):
        response = self.client.get(self.team_1)
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.user)

        response = self.client.get(self.team_1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            "id": 1,
            "name": "first-team",
            "project": 1
        })

        response = self.client.get(self.team_2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            "id": 2,
            "name": "test",
            "project": 1
        })

        response = self.client.get(reverse('gantt:team-detail', kwargs={'pk': self.team_id_for_username1}))
        self.assertEqual(response.status_code, 404)

    def test_put_team(self):
        response = self.client.put(self.team_1, {
            'name': 'amir',
            'project': 1
        })
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.user)

        response = self.client.put(self.team_1, data={
            'name': 'first-team edited',
            'project': 1
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            'id': 1,
            'name': 'first-team edited',
            'project': 1
        })

        response = self.client.put(self.team_1, data={
            'name': 'first-team edited',
            'project': 2
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            'id': 1,
            'name': 'first-team edited',
            'project': 2
        })

        response = self.client.put(self.team_1, data={
            'name': 'first-team edited',
            'project': 3
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, 'the project must be for itself.')

        url = reverse('gantt:team-detail', args=(321,))

        response = self.client.put(url, data={
            'name': 'something',
            'project': 1
        })
        self.assertEqual(response.status_code, 404)

    def test_patch_team(self):
        response = self.client.patch(self.team_1, {
            'name': 'amir',
        })
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.user)

        response = self.client.patch(self.team_1, data={
            'name': 'first-team edited',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            'id': 1,
            'name': 'first-team edited',
            'project': 1
        })

        response = self.client.patch(self.team_1, data={
            'project': 2
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            'id': 1,
            'name': 'first-team edited',
            'project': 2
        })

        response = self.client.patch(self.team_1, data={
            'project': 3
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, 'the project must be for itself.')

        url = reverse('gantt:team-detail', args=(321,))

        response = self.client.patch(url, data={
            'name': 'something',
        })
        self.assertEqual(response.status_code, 404)

    def test_delete_team(self):
        response = self.client.delete(self.team_1)
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.user)

        self.assertTrue(Team.objects.filter(id=1).exists())

        response = self.client.delete(self.team_1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Team.objects.filter(id=1).exists())

        url = reverse('gantt:team-detail', kwargs={'pk': self.team_id_for_username1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Team.objects.filter(id=self.team_id_for_username1).exists())

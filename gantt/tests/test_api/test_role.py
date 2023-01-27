from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from gantt.models import Role
from gantt.tests.base import GanttMixin


class TestCreateRole(GanttMixin, APITestCase):

    def setUp(self) -> None:
        self.role_list_url = reverse('gantt:role-list')

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

        # create a project for 'username1'
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

        self.client.logout()

    def test_create_role(self):
        response = self.client.post(self.role_list_url, data={
            'project': 1,
            'name': 'nothing'
        })
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)

        response = self.client.post(self.role_list_url, data={
            'project': 1,
            'name': 'First Role'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {
            'id': 1,
            'project': 1,
            'name': 'First Role'
        })

        response = self.client.post(self.role_list_url, data={
            'project': 1,
            'name': 'Second Role'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {
            'id': 2,
            'project': 1,
            'name': 'Second Role'
        })

        response = self.client.post(self.role_list_url, data={
            'project': 2,
            'name': '3rd Role'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {
            'id': 3,
            'project': 2,
            'name': '3rd Role'
        })

        response = self.client.post(self.role_list_url, data={
            'project': 3,
            'name': 'not ok'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, "user must not use other users' projects.")
        self.assertEqual(response.data, {
            "project": [
                "Invalid pk \"3\" - object does not exist."
            ]
        })

        response = self.client.post(self.role_list_url, data={
            'project': '1d',
            'name': 'the name'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            "project": [
                "Incorrect type. Expected pk value, received str."
            ]
        })

        response = self.client.post(self.role_list_url, format='json', data={
            'project': {'id': 1},
            'name': 'the name'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            "project": [
                "Incorrect type. Expected pk value, received dict."
            ]
        })

        response = self.client.post(self.role_list_url, format='json', data={
            'project': [{'id': 1}],
            'name': 'the name'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            "project": [
                "Incorrect type. Expected pk value, received list."
            ]
        })

        response = self.client.post(self.role_list_url, format='json', data={
            'project': 1,
            'name': ''
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            "name": [
                "This field may not be blank."
            ]
        })

        self.client.logout()
        self.client.force_login(self.username1)

        response = self.client.post(self.role_list_url, data={
            'project': 3,
            'name': 'role for username1'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {
            'id': 4,
            'project': 3,
            'name': 'role for username1'
        })

        response = self.client.post(self.role_list_url, data={
            'project': 1,
            'name': 'no role'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            "project": [
                "Invalid pk \"1\" - object does not exist."
            ]
        })

        response = self.client.post(self.role_list_url, data={
            'project': 3,
            'name': 'role for username1'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {
            'id': 5,
            'project': 3,
            'name': 'role for username1'
        }, msg='the name is duplicate.')


class TestRole(GanttMixin, APITestCase):
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

        url = reverse('gantt:role-list')
        id_1 = self.client.post(url, {
            'name': 'first-role',
            'project': 1
        }).data['id']
        assert id_1 == 1

        id_2 = self.client.post(url, {
            'name': 'test1',
            'project': 1
        }).data['id']
        assert id_2 == 2

        self.client.post(url, {
            'name': 'amir ',
            'project': 1
        })

        self.client.logout()

        self.role_1 = reverse('gantt:role-detail', kwargs={'pk': id_1})
        self.role_2 = reverse('gantt:role-detail', kwargs={'pk': id_2})

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

        url = reverse('gantt:role-list')
        id_u1 = self.client.post(url, {
            'name': 'A Role for Username1',
            'project': 3
        }).data['id']
        assert id_u1 == 4
        self.role_id_for_username1 = id_u1

        self.client.logout()

    def test_get_role(self):
        response = self.client.get(self.role_1)
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)

        response = self.client.get(self.role_1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            'id': 1,
            'name': 'first-role',
            'project': 1
        })

        response = self.client.get(self.role_2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            'id': 2,
            'name': 'test1',
            'project': 1
        })

        response = self.client.get(reverse('gantt:role-detail', kwargs={'pk': self.role_id_for_username1}))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {
            "detail": "Not found."
        })

    def test_put_role(self):
        response = self.client.put(self.role_1, {
            'name': 'amir\'s role',
            'project': 1
        })
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)

        response = self.client.put(self.role_1, data={
            'name': 'first-role edited',
            'project': 1
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            'id': 1,
            'name': 'first-role edited',
            'project': 1
        })

        response = self.client.put(self.role_1, data={
            'name': 'first-role edited',
            'project': 2
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            'id': 1,
            'name': 'first-role edited',
            'project': 2
        })

        response = self.client.put(self.role_1, data={
            'name': 'first-role edited',
            'project': 3
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, 'the project must be for itself.')

        url = reverse('gantt:role-detail', args=(321,))

        response = self.client.put(url, data={
            'name': 'something',
            'project': 1
        })
        self.assertEqual(response.status_code, 404)

        url = reverse('gantt:role-detail', args=(self.role_id_for_username1,))

        response = self.client.put(url, data={
            'name': 'something',
            'project': 1
        })
        self.assertEqual(response.status_code, 404)

        response = self.client.put(self.role_1, data={
            'name': 'first-role edited'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            "project": [
                "This field is required."
            ]
        }, msg='project must be present.')

        response = self.client.put(self.role_1, data={
            'project': 1
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            "name": [
                "This field is required."
            ]
        })

        response = self.client.put(self.role_1, data={
            'name': '',
            'project': 1
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            "name": [
                "This field may not be blank."
            ]
        })

    def test_patch_role(self):
        response = self.client.patch(self.role_1, {
            'name': 'amir',
        })
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)

        response = self.client.patch(self.role_1, data={
            'name': 'first-role edited',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            'id': 1,
            'name': 'first-role edited',
            'project': 1
        })

        response = self.client.patch(self.role_1, data={
            'project': 2
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            'id': 1,
            'name': 'first-role edited',
            'project': 2
        })

        response = self.client.patch(self.role_1, data={
            'project': 3
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, 'the project must be for itself.')

        url = reverse('gantt:role-detail', args=(321,))

        response = self.client.patch(url, data={
            'name': 'something',
        })
        self.assertEqual(response.status_code, 404)

        response = self.client.patch(self.role_1, data={
            'name': ''
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.patch(reverse('gantt:role-detail', kwargs={'pk': self.role_id_for_username1}), data={
            'name': 'username1 Role error'
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_role(self):
        response = self.client.delete(self.role_1)
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)

        self.assertTrue(Role.objects.filter(id=1).exists())

        response = self.client.delete(self.role_1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Role.objects.filter(id=1).exists())

        url = reverse('gantt:team-detail', kwargs={'pk': self.role_id_for_username1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Role.objects.filter(id=self.role_id_for_username1).exists())

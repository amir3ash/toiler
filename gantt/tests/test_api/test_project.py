from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from gantt.models import Project
from gantt.serializers import ProjectSerializer
from gantt.tests.base import GanttMixin


class TestProject(GanttMixin, APITestCase):
    def setUp(self) -> None:
        self.project_list = reverse('gantt:project-list')

    def test_request_without_login(self):
        msg = f'Request on "{self.project_list}" without credentials must return 403 status code.'
        response = self.client.get(self.project_list)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, msg)

        response = self.client.head(self.project_list)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, msg)

        response = self.client.post(self.project_list)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, msg)

        response = self.client.put(self.project_list)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, msg)

        response = self.client.patch(self.project_list)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, msg)

        response = self.client.options(self.project_list)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, msg)

        response = self.client.trace(self.project_list)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, msg)

        response = self.client.delete(self.project_list)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, msg)

        url = reverse('gantt:project-detail', kwargs={'pk': 1})

        msg = f'Request on "{url}" without credentials must return 403 status code.'

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, msg)

        response = self.client.head(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, msg)

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, msg)

        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, msg)

        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, msg)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, msg)

        response = self.client.trace(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, msg)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, msg)

    def test_create_project(self):
        self.client.force_login(self.user)

        response = self.client.post(self.project_list, data={
            "name": "Test Project",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2021-09-10",
            "actual_start_date": "2021-09-01",
            "actual_end_date": "2021-09-02",
            "description": "this is test for project"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get(id=response.data['id'])
        self.assertEqual(response.data, ProjectSerializer(project).data)

        self.assertEqual(Project.objects.all().count(), 1)

        response = self.client.post(self.project_list, data={
            "id": 3,
            "name": "Test Project Two",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2021-09-10",
            "actual_start_date": "2021-09-01",
            "actual_end_date": "2021-09-02",
            "description": "this is test for project Two"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get(id=response.data['id'])
        self.assertEqual(response.data, ProjectSerializer(project).data)
        self.assertEqual(Project.objects.all().count(), 2)

    def test_put_project(self):
        self.client.force_login(self.user)
        response = self.client.post(self.project_list, data={
            "name": "first",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2021-09-10",
            "actual_start_date": "2021-09-01",
            "actual_end_date": "2021-09-02",
            "description": "this is t"
        })
        first_id, first_description = response.data['id'], response.data['description']

        second_id = self.client.post(self.project_list, data={
            "name": "2nd",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2021-09-10",
            "actual_start_date": "2021-09-01",
            "actual_end_date": "2021-09-02",
        }).data['id']

        url = reverse('gantt:project-detail', kwargs={'pk': first_id})
        response = self.client.put(url, data={
            "id": first_id,
            "name": "2nd ii",
            "planned_start_date": "2021-08-30",
            "planned_end_date": "2021-09-10",
            "actual_start_date": "2021-09-02",
            "actual_end_date": "2021-09-03",
        })
        self.assertEqual(response.status_code, 200)
        project = Project.objects.get(id=response.data['id'])
        self.assertEqual(response.data, ProjectSerializer(project).data, 'description should be not empty.')

        url = reverse('gantt:project-detail', kwargs={'pk': second_id})
        response = self.client.put(url, data={
            "id": second_id,
            "name": "2nd",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2021-09-11",
            "actual_start_date": "2021-09-06",
        })
        self.assertEqual(response.status_code, 200, 'actual_end_date can be null.')

        url = reverse('gantt:project-detail', kwargs={'pk': second_id})
        response = self.client.put(url, data={
            "id": first_id,
            "name": "2nd",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2021-09-11",
            "actual_start_date": "2021-09-06",
            "actual_end_date": "2021-10-30"
        })
        self.assertEqual(response.status_code, 200)
        project = Project.objects.get(id=response.data['id'])
        self.assertEqual(response.data, ProjectSerializer(project).data, "Api must consider 'id' in url and ignore "
                                                                         "'id' in json.")

        self.client.logout()
        self.client.force_login(self.username2)

        response = self.client.put(url, data={
            "id": second_id,
            "name": "2nd",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2021-09-11",
            "actual_start_date": "2021-09-06",
            "actual_end_date": "2021-10-30"
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.put(url, data={
            "name": "2nd",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2021-09-11",
            "actual_start_date": "2021-09-06",
            "actual_end_date": "2021-10-30"
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url = reverse('gantt:project-detail', kwargs={'pk': 3})
        response = self.client.put(url, data={
            "name": "3rd for new user",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2021-09-11",
            "actual_start_date": "2021-09-06",
            "actual_end_date": "2021-10-30"
        })
        self.assertEqual(response.status_code, 404, 'it must not allow to create new object via put method.')

        url = reverse('gantt:project-detail', kwargs={'pk': 4})
        response = self.client.put(url, data={
            "id": 4,
            "name": "4th for new user",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2021-09-11",
            "actual_start_date": "2021-09-06",
            "actual_end_date": "2021-10-30"
        })
        self.assertEqual(response.status_code, 404, 'it must not allow to create new object via put method.')

    def test_get_project(self):
        self.client.force_login(self.user)
        first_id = self.client.post(self.project_list, data={
            "name": "first",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2021-09-10",
            "actual_start_date": "2021-09-01",
            "actual_end_date": "2021-09-02",
            "description": "this is t"
        }).data['id']
        second_id = self.client.post(self.project_list, data={
            "name": "2nd",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2021-09-10",
            "actual_start_date": "2021-09-01",
            "actual_end_date": "2021-09-02",
        }).data['id']

        url = reverse('gantt:project-detail', kwargs={'pk': first_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        url = reverse('gantt:project-detail', kwargs={'pk': second_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.client.logout()
        self.client.force_login(self.username2)

        response = self.client.get(self.project_list)
        self.assertEqual(response.data, [], 'User without project, must not get others project.')

        url = reverse('gantt:project-detail', kwargs={'pk': second_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_patch_project(self):
        self.client.force_login(self.username1)
        response = self.client.post(self.project_list, data={
            "name": "first project",
            "planned_start_date": "2010-08-31",
            "planned_end_date": "2021-09-10",
            "actual_start_date": "2021-09-01",
            "actual_end_date": "2022-09-02",
            "description": "this is t"
        })
        first_id = response.data['id']

        second_id = self.client.post(self.project_list, data={
            "name": "2nd",
            "planned_start_date": "2021-08-31",
            "planned_end_date": "2021-09-10",
            "actual_start_date": "2021-09-01",
            "actual_end_date": "2021-09-02"
        }).data['id']

        first_url = reverse('gantt:project-detail', kwargs={'pk': first_id})
        second_url = reverse('gantt:project-detail', kwargs={'pk': second_id})

        response = self.client.patch(first_url, data={
            'name': 'amirProj'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            "id": first_id,
            "project_manager": self.username1.id,
            'name': 'amirProj',
            "planned_start_date": "2010-08-31",
            "planned_end_date": "2021-09-10",
            "actual_start_date": "2021-09-01",
            "actual_end_date": "2022-09-02",
            "description": "this is t",
        }, msg='response should contain all fields and `name` must be changed.')

        response = self.client.patch(second_url, data={
            'name': 'helloProj',
            'actual_end_date': '2023-01-01'
        })
        self.assertEqual(response.status_code, 200)
        project = Project.objects.get(id=second_id)
        self.assertEqual(response.data, ProjectSerializer(project).data)

        self.client.logout()

        response = self.client.patch(second_url, data={
            'name': 'helloProj',
            'actual_end_date': '2023-01-01'
        })
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.username2)

        self.client.post(self.project_list, {
            "name": "user 3 project",
            "planned_start_date": "2015-08-31",
            "planned_end_date": "2028-09-10",
            "actual_start_date": "2021-09-01",
            "actual_end_date": "2022-09-02",
            "description": "other"
        })

        response = self.client.patch(first_url, data={
            'name': ''
        })
        self.assertEqual(response.status_code, 404)

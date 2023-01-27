import datetime

from django.urls import reverse
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase

from gantt.models import TeamMember, Role, Team, Project
from gantt.serializers import TeamMemberSerializer
from gantt.tests.base import GanttMixin, _create_user


class TestCreateTeamMember(GanttMixin, APITestCase):
    def setUp(self) -> None:
        self.team_member_url = reverse('gantt:team-member-list')

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

        team_url = reverse('gantt:team-list')

        # creating teams for the main user
        team1 = self.client.post(team_url, data={
            'name': 'First team',
            'project': self.project1_id
        })
        assert team1.status_code == 201
        self.team1_id = team1.data['id']

        team2 = self.client.post(team_url, data={
            'name': 'Second team',
            'project': self.project1_id
        })
        assert team2.status_code == 201
        self.team2_id = team2.data['id']

        role_url = reverse('gantt:role-list')

        # creating roles for the main user
        role1 = self.client.post(role_url, data={
            'name': 'First role',
            'project': self.project1_id
        })
        assert role1.status_code == 201
        self.role1_id = team1.data['id']

        role2 = self.client.post(role_url, data={
            'name': 'Second role',
            'project': self.project1_id
        })
        assert role2.status_code == 201
        self.role2_id = role2.data['id']

        role3 = self.client.post(role_url, data={
            'name': '3rd role for project 2',
            'project': self.project2_id
        })
        assert role3.status_code == 201
        self.role3_id = role3.data['id']

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

        # create a team for username1
        other_team = self.client.post(team_url, {
            'name': 'A team for username1',
            'project': self.project_id_for_username1
        })
        assert other_team.status_code == 201
        self.team_id_for_username1 = other_team.data['id']

        # create a role for username1
        other_role = self.client.post(team_url, {
            'name': 'A role for username1',
            'project': self.project_id_for_username1
        })
        assert other_role.status_code == 201
        self.role_id_for_username1 = other_role.data['id']

        self.client.logout()

    def test_create_team_member(self):
        response = self.client.post(self.team_member_url)
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)

        response = self.client.post(self.team_member_url, data={
            'team': self.team1_id,
            'role': self.role1_id,
            'user': self.username1.id
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {
            'id': 1,
            'team': self.team1_id,
            'role': self.role1_id,
            'user': self.username1.id
        })

        response = self.client.post(self.team_member_url, data={
            'team': self.team1_id,
            'role': self.role2_id,
            'user': self.username1.id
        })
        self.assertEqual(response.status_code, 400, msg='same employees and teams should return error.'
                                                        ' -> "unique together"')

        response = self.client.post(self.team_member_url, data={
            'team': self.team1_id,
            'role': self.role2_id,
            'user': self.username1.id  # this employee is for project 2
        })
        self.assertEqual(response.status_code, 400, msg='team,role,employee must have same project')
        # self.assertEqual(response.content, b'{"non_field_errors":["projects not match."]}')

        response = self.client.post(self.team_member_url, data={
            'team': self.team_id_for_username1,
            'role': self.role2_id,
            'user': self.username1.id
        })
        self.assertEqual(response.status_code, 400, msg='should return team does not exist.')
        self.assertEqual(response.data, {
            'team': [
                f'Invalid pk "{self.team_id_for_username1}" - object does not exist.'
            ]
        })

        response = self.client.post(self.team_member_url, data={
            'team': self.team_id_for_username1,
            'role': self.role2_id,
            'user': self.user.id
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'team': [
                ErrorDetail(string=f'Invalid pk "{self.team_id_for_username1}" - object does not exist.',
                            code='does_not_exist')
            ],
            # 'user': [
            #     ErrorDetail(string=f'Invalid pk "{self.user.id}" - object does not exist.',
            #                 code='does_not_exist')
            # ]
        })

        response = self.client.post(self.team_member_url, data={
            'id': 10,
            'team': self.team2_id,
            'role': self.role2_id,
            'user': self.username1.id
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {
            'id': 2,
            'team': self.team2_id,
            'role': self.role2_id,
            'user': self.username1.id
        })


class TestTeamMember(GanttMixin, APITestCase):
    def setUp(self) -> None:
        test_user2 = _create_user('t2')

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

    def test_get_team_member(self):
        url = reverse('gantt:team-member-detail', kwargs={'pk': self.member1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, TeamMemberSerializer(self.member1).data)

        url = reverse('gantt:team-member-detail', kwargs={'pk': self.member2.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, TeamMemberSerializer(self.member2).data)

        url = reverse('gantt:team-member-detail', kwargs={'pk': self.member3.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'he should access that. the project is for him')
        self.assertEqual(response.data, TeamMemberSerializer(self.member3).data)

        url = reverse('gantt:team-member-detail', kwargs={'pk': self.member_u1.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_put_team_member(self):
        url = reverse('gantt:team-member-detail', kwargs={'pk': self.member1.id})
        response = self.client.put(url)
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)

        response = self.client.put(url, data={
            'id': self.member1.id,
            'role': self.member1.role.id
        })
        self.assertEqual(response.status_code, 400, 'returns error. because team field not exists.')

        response = self.client.put(url, data={
            'id': self.member1.id,
            'team': self.member1.team.id,
            'role': self.member1.role.id,
            # 'user': self.member1.user.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, TeamMemberSerializer(self.member1).data)

        response = self.client.put(url, data={
            'id': self.member1.id,
            'team': self.team_for_user.id,  # team_for_user is for project2
            'role': self.member1.role.id,
            # 'user': self.member1.user.id
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'non_field_errors': [ErrorDetail(string='projects not match.', code='invalid')]
        })

        response = self.client.put(url, data={
            'id': self.member1.id,
            'team': self.team_for_username1.id,
            'role': self.member1.role.id
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'team': [
                ErrorDetail(string=f'Invalid pk "{self.team_for_username1.id}" - object does not exist.',
                            code='does_not_exist')
            ]
        })

        response = self.client.put(url, data={
            'id': self.member1.id,
            'team': 201,
            'role': self.member1.role.id
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'team': [
                ErrorDetail(string=f'Invalid pk "201" - object does not exist.', code='does_not_exist')
            ]
        })

        # url = reverse('team-member-detail', kwargs={'pk': self.member2.id})
        # url = reverse('team-member-detail', kwargs={'pk': self.member3.id})
        url = reverse('gantt:team-member-detail', kwargs={'pk': self.member_u1.id})

        response = self.client.put(url, data={
            'id': self.member1.id,
            'team': 201,
            'role': self.member1.role.id
        })
        self.assertEqual(response.status_code, 404)

    def test_patch_team_member(self):
        url = reverse('gantt:team-member-detail', kwargs={'pk': self.member1.id})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.user)

        response = self.client.patch(url, data={
            'role': self.member1.role.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            'id': self.member1.id,
            'team': self.member1.team.id,
            'user': self.member1.user.id,
            'role': self.member1.role.id
        })

        response = self.client.patch(url, data={
            'team': self.member1.team.id,
            'role': self.member1.role.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {
            'id': self.member1.id,
            'team': self.member1.team.id,
            'user': self.member1.user.id,
            'role': self.member1.role.id
        })

        response = self.client.patch(url, data={
                'team': self.team_for_user.id,  # team_for_user is for project2
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'non_field_errors': [ErrorDetail(string='projects not match.', code='invalid')]
        })

        response = self.client.patch(url, data={
            'team': self.team_for_username1.id,
            'role': self.member1.role.id
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'team': [
                ErrorDetail(string=f'Invalid pk "{self.team_for_username1.id}" - object does not exist.',
                            code='does_not_exist')
            ]
        })

        response = self.client.patch(url, data={
            'team': self.team_for_username1.id
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'team': [
                ErrorDetail(string=f'Invalid pk "{self.team_for_username1.id}" - object does not exist.',
                            code='does_not_exist')
            ]
        })

        response = self.client.patch(url, data={
            'id': 21,
            'team': 201,
            'role': self.member1.role.id
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'team': [
                ErrorDetail(string=f'Invalid pk "201" - object does not exist.', code='does_not_exist')
            ]
        })

        url = reverse('gantt:team-member-detail', kwargs={'pk': self.member_u1.id})

        response = self.client.patch(url, data={
            'id': self.member1.id,
            'team': 201,
            'role': self.member1.role.id
        })
        self.assertEqual(response.status_code, 404)

    def test_delete_team_member(self):
        url = reverse('gantt:team-member-detail', kwargs={'pk': self.member1.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 401)
        self.assertTrue(TeamMember.objects.filter(id=self.member1.id).exists())

        self.client.force_login(self.user)

        response = self.client.delete(url, data={
            'role': self.member1.role.id
        })
        self.assertEqual(response.status_code, 204)
        self.assertFalse(TeamMember.objects.filter(id=self.member1.id).exists())

        url = reverse('gantt:team-member-detail', kwargs={'pk': self.member_u1.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(TeamMember.objects.filter(id=self.member_u1.id).exists())

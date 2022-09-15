import datetime

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from gantt.models import Task, Role, Team, TeamMember, Project, State, Activity, Assigned
from gantt.serializers import AssignedSerializer
from gantt.tests.base import GanttMixin, _create_user


class TestCreateAssigned(GanttMixin, APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse('gantt:assigned-list')

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
        cls.role1 = Role.objects.create(name='Manager', project=cls.project1)
        cls.role2 = Role.objects.create(name='Second role', project=cls.project1)
        cls.role3 = Role.objects.create(name='3rd role', project=cls.project2)
        cls.role_for_username1 = Role.objects.create(name='4th role', project=cls.project_for_usrname1)

        # # update assistant role
        # cls.project1.assistant_role = cls.role1
        # cls.project1.save()

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

        # create activities
        cls.activity1 = Activity.objects.create(name='ac1', task=cls.task1, planned_start_date=now,
                                                planned_end_date=now + datetime.timedelta(days=5))

        cls.activity2 = Activity.objects.create(name='ac2', task=cls.task1, planned_start_date=now,
                                                planned_end_date=now + datetime.timedelta(hours=20))

        cls.activity3 = Activity.objects.create(name='ac3', task=cls.task2, planned_start_date=now,
                                                planned_end_date=now + datetime.timedelta(days=53))

        cls.activity_for_project2 = Activity.objects.create(name='ac p2', task=cls.task3, planned_start_date=now,
                                                            planned_end_date=now + datetime.timedelta(days=56))

        cls.activity_u1 = Activity.objects.create(name='ac u1', task=cls.task_u1, planned_start_date=now,
                                                  planned_end_date=now + datetime.timedelta(days=25))

        cls.activity_test_user = Activity.objects.create(name='ac tu2', task=cls.task_test_user,
                                                         planned_start_date=now,
                                                         planned_end_date=now + datetime.timedelta(days=17))

    def test_create(self):
        response = self.client.post(self.url, data={
            'activity': '',
            'user': ''
        })
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.user)

        # normal request
        response = self.client.post(self.url, data={
            'activity': self.activity1.id,
            'user': self.username1.id
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {
            'id': 1,
            'user': self.username1.id,
            'activity': self.activity1.id
        })
        self.assertEqual(response.data, AssignedSerializer(Assigned.objects.get(id=1)).data)

    def test_create_with_project_manager(self):
        # test: user is project manager but not team_member of that project.

        self.client.force_login(self.user)

        response = self.client.post(self.url, data={
            'activity': self.activity1.id,
            'user': self.user.id
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'user': [f'Invalid pk "{self.user.id}" - object does not exist.']})

    def test_with_team_member(self):
        # test: user is team_member project_manager and username1 is employee of the project.

        self.client.force_login(self.user)

        response = self.client.post(self.url, data={
            'activity': self.activity2.id,
            'user': self.username1.id
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, AssignedSerializer(Assigned.objects.get(id=1)).data)

    def test_with_others_activity(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, data={
            'activity': self.activity_u1.id,
            'user': self.username1.id
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'activity': [f'Invalid pk "{self.activity_u1.id}" - object does not exist.']})



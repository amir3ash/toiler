import datetime

from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from gantt.models import Project, Team, Role, TeamMember, State, Task, Activity, Comment
from gantt.serializers import CommentSerializer
from gantt.tests.base import GanttMixin, _create_user


class TestCreateComment(GanttMixin, APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse('gantt:comment-list')

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
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.user)

        # normal request
        response = self.client.post(self.url, data={
            'text': 'text',
            'activity': self.activity1.id
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(list(response.data.keys()), ['id', 'author', 'activity', 'created_at', 'updated_at', 'text'])
        self.assertEqual(response.data, CommentSerializer(Comment.objects.get(id=1)).data)

    def test_without_activity(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, data={
            'text': 'text',
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'activity': ['This field is required.']})

    def test_with_team_member(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, data={
            'text': 'text',
            'activity': self.activity_u1.id
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, CommentSerializer(Comment.objects.get(id=1)).data)

    def test_with_others_activity(self):
        self.client.force_login(self.test_user2)

        response = self.client.post(self.url, data={
            'text': 'text',
            'activity': self.activity_u1.id
        })
        self.assertEqual(response.status_code, 400, "he isn't project_manager neither team_member of project1")
        self.assertEqual(response.data, {'activity': [f'Invalid pk "{self.activity_u1.id}" - object does not exist.']})

        response = self.client.post(self.url, data={
            'text': 'text',
            'activity': 3535
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'activity': ['Invalid pk "3535" - object does not exist.']})

    def test_with_time(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, data={
            'text': 'text',
            'activity': self.activity1.id,
            'created_at': '2021-08-31T00:00',
            'updated_at': '2021-08-31T00:00'
        })
        self.assertEqual(response.status_code, 201)
        comment = Comment.objects.get(id=1)
        self.assertEqual(response.data, CommentSerializer(comment).data)
        self.assertTrue(comment.created_at > datetime.datetime.fromisoformat('2021-08-31T00:00+00:00'))
        self.assertTrue(comment.updated_at > datetime.datetime.fromisoformat('2021-08-31T00:00+00:00'))


class TestComment(GanttMixin, APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

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

    def setUp(self):
        self.comment1 = Comment.objects.create(text='text', author=self.user, activity=self.activity1)
        self.comment2 = Comment.objects.create(text='text', author=self.user, activity=self.activity2)
        self.comment3 = Comment.objects.create(text='text', author=self.user, activity=self.activity3)
        self.comment_u1 = Comment.objects.create(text='text', author=self.username1, activity=self.activity_u1)
        self.comment_test_user = Comment.objects.create(text='text', author=self.test_user2,
                                                        activity=self.activity_test_user)

    def test_get(self):
        url = reverse('gantt:comment-detail', kwargs={'pk': self.comment1.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, CommentSerializer(self.comment1).data)

        url = reverse('gantt:comment-detail', kwargs={'pk': self.comment_u1.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, 'he is team_member of its project.')
        self.assertEqual(response.data, CommentSerializer(self.comment_u1).data)

        url = reverse('gantt:comment-detail', kwargs={'pk': self.comment_test_user.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404, "he isn't team_member or project_manager of its project.")

    def test_put(self):
        url = reverse('gantt:comment-detail', kwargs={'pk': self.comment1.id})

        self.client.force_login(self.user)

        response = self.client.put(url, data={
            'text': 'a'
        })
        self.assertEqual(response.status_code, 200)
        self.comment1.refresh_from_db()
        self.assertEqual(response.data, CommentSerializer(self.comment1).data)

        url = reverse('gantt:comment-detail', kwargs={'pk': self.comment_u1.id})

        response = self.client.put(url, data={
            'text': 'text'
        })
        self.assertEqual(response.status_code, 403, 'he is not author of the comment.')
        self.assertEqual(response.data, {'detail': 'You do not have permission to perform this action.'})

        url = reverse('gantt:comment-detail', kwargs={'pk': self.comment_test_user.id})

        response = self.client.put(url, data={
            'text': 'text'
        })
        self.assertEqual(response.status_code, 404, 'he can not view the comment')

    def test_delete(self):
        url = reverse('gantt:comment-detail', kwargs={'pk': self.comment1.id})

        self.client.force_login(self.user)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Comment.objects.filter(id=self.comment1.id))

        url = reverse('gantt:comment-detail', kwargs={'pk': self.comment_u1.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403, 'he is not author of the comment.')
        self.assertEqual(response.data, {'detail': 'You do not have permission to perform this action.'})
        self.assertTrue(Comment.objects.filter(id=self.comment_u1.id))

        url = reverse('gantt:comment-detail', kwargs={'pk': self.comment_test_user.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404, 'he can not view the comment')
        self.assertTrue(Comment.objects.filter(id=self.comment_test_user.id))


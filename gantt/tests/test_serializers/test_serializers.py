import django
import os
from django.test import SimpleTestCase

# from rest_framework.exceptions import ErrorDetail

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Toiler.settings")
os.environ.setdefault("LOCAL_AREA", '1')
django.setup()
del os, django

# from gantt.models import Project
from gantt.serializers import (
    ProjectSerializer, ProjectWithRelatedSerializer,
    TaskSerializer, TaskUpdateSerializer,
    ActivitySerializer,
    TeamSerializer,
    RoleSerializer,
    TeamMemberSerializer, TeamMemberGetSerializer, VerboseTeamMemberSerializer,
    StateSerializer, StateUpdateSerializer,
    CommentSerializer, CommentOnlyChangeTextSerializer,
    AssignedSerializer, AssignedUpdateSerializer,
)


# from rest_framework.test import APIRequestFactory, APITestCase
# from gantt.tests.base import GanttMixin


class TestFieldsMixin:
    required_fields = []
    fields = []
    read_only_fields = []
    write_only_fields = []
    serializer_class = None

    def test_required_fields(self):
        assert self.serializer_class is not None

        serializer = self.serializer_class(data={})

        required_fields = set(self.required_fields)

        actual_required = {
            field_name for field_name, field in serializer.fields.items()
            if field.required
        }
        diff = required_fields.symmetric_difference(actual_required)

        self.assertEqual(set(), diff, f'required fields must be {self.required_fields}')

    def test_all_fields(self):
        serializer = self.serializer_class()

        fields = set(self.fields)

        actual_fields = {
            field_name for field_name in serializer.fields
        }
        diff = fields.symmetric_difference(actual_fields)

        self.assertEqual(set(), diff, f'all fields must be {self.fields}')

    def test_read_only_fields(self):
        read_only_fields = set(self.read_only_fields)
        meta_read_only_fields = set(getattr(self.serializer_class.Meta, 'read_only_fields', {}))

        actual_readonly = {
            field_name for field_name, field in self.serializer_class().fields.items()
            if field.read_only
        }
        actual_readonly = actual_readonly.union(meta_read_only_fields)
        diff = read_only_fields.symmetric_difference(actual_readonly)

        self.assertEqual(set(), diff, f'read only fields must be {self.read_only_fields}')


class TestProjectSerializer(TestFieldsMixin, SimpleTestCase):
    serializer_class = ProjectSerializer
    fields = ['id', 'name', 'planned_start_date', 'planned_end_date', 'actual_start_date', 'actual_end_date',
              'description', 'project_manager']
    required_fields = ['name', 'planned_start_date', 'planned_end_date']
    read_only_fields = ['id', 'project_manager']
    write_only_fields = []


class TestTaskSerializer(TestFieldsMixin, SimpleTestCase):
    serializer_class = TaskSerializer
    fields = ['id', 'project', 'name', 'planned_start_date', 'planned_end_date', 'actual_start_date', 'actual_end_date',
              'planned_budget', 'actual_budget', 'description']
    required_fields = ['project', 'name', 'planned_start_date', 'planned_end_date', 'planned_budget', 'actual_budget']
    read_only_fields = ['id']
    write_only_fields = []


class TestTaskUpdateSerializer(TestFieldsMixin, SimpleTestCase):
    serializer_class = TaskUpdateSerializer
    fields = ['id', 'project', 'name', 'planned_start_date', 'planned_end_date', 'actual_start_date',
              'actual_end_date',
              'planned_budget', 'actual_budget', 'description']
    required_fields = ['name', 'planned_start_date', 'planned_end_date', 'planned_budget',
                       'actual_budget']
    read_only_fields = ['id', 'project']
    write_only_fields = []


class TestActivitySerializer(TestFieldsMixin, SimpleTestCase):
    serializer_class = ActivitySerializer
    fields = ['id', 'task', 'name', 'planned_start_date', 'planned_end_date', 'actual_start_date', 'actual_end_date',
              'planned_budget', 'actual_budget', 'description', 'dependency', 'state']
    required_fields = ['task', 'name', 'planned_start_date', 'planned_end_date']
    read_only_fields = ['id']
    write_only_fields = []


class TestTeamSerializer(TestFieldsMixin, SimpleTestCase):
    serializer_class = TeamSerializer
    fields = ['id', 'project', 'name']
    required_fields = ['project', 'name']
    read_only_fields = ['id']
    write_only_fields = []


class TestRoleSerializer(TestFieldsMixin, SimpleTestCase):
    serializer_class = RoleSerializer
    fields = ['id', 'project', 'name']
    required_fields = ['project', 'name']
    read_only_fields = ['id']
    write_only_fields = []


class TestTeamMemberSerializer(TestFieldsMixin, SimpleTestCase):
    serializer_class = TeamMemberSerializer
    fields = ['id', 'team', 'role', 'user']
    required_fields = ['team', 'user', 'role']
    read_only_fields = ['id']
    write_only_fields = []


class TestTeamMemberGetSerializer(TestFieldsMixin, SimpleTestCase):
    serializer_class = TeamMemberGetSerializer
    fields = ['id', 'team', 'user', 'role']
    required_fields = ['team', 'role']
    read_only_fields = ['id', 'user']
    write_only_fields = []


class TestVerboseTeamMemberSerializer(TestFieldsMixin, SimpleTestCase):
    serializer_class = VerboseTeamMemberSerializer
    fields = ['id', 'team', 'user', 'role']
    required_fields = []
    read_only_fields = ['id', 'team', 'user', 'role']
    write_only_fields = []


class TestStateSerializer(TestFieldsMixin, SimpleTestCase):
    serializer_class = StateSerializer
    fields = ['id', 'name', 'project']
    required_fields = ['name', 'project']
    read_only_fields = ['id']
    write_only_fields = []


class TestStateUpdateSerializer(TestFieldsMixin, SimpleTestCase):
    serializer_class = StateUpdateSerializer
    fields = ['id', 'name', 'project']
    required_fields = ['name']
    read_only_fields = ['id', 'project']
    write_only_fields = []


class TestCommentSerializer(TestFieldsMixin, SimpleTestCase):
    serializer_class = CommentSerializer
    fields = ['id', 'text', 'author', 'activity', 'created_at', 'updated_at']
    required_fields = ['text', 'activity']
    read_only_fields = ['id', 'author', 'created_at', 'updated_at']
    write_only_fields = []


class TestCommentOnlyChangeTextSerializer(TestFieldsMixin, SimpleTestCase):
    serializer_class = CommentOnlyChangeTextSerializer
    fields = ['id', 'text', 'author', 'activity', 'created_at', 'updated_at']
    required_fields = ['text']
    read_only_fields = ['id', 'author', 'activity', 'created_at', 'updated_at']
    write_only_fields = []


class TestAssignedSerializer(TestFieldsMixin, SimpleTestCase):
    serializer_class = AssignedSerializer
    fields = ['id', 'user', 'activity']
    required_fields = ['user', 'activity']
    read_only_fields = ['id']
    write_only_fields = []


class TestAssignedUpdateSerializer(TestFieldsMixin, SimpleTestCase):
    serializer_class = AssignedUpdateSerializer
    fields = ['id', 'user', 'activity']
    required_fields = ['user']
    read_only_fields = ['id', 'activity']
    write_only_fields = []

# class Test(GanttMixin, APITestCase):
#
#     def test_(self):
#         request_factory = APIRequestFactory()
#         request = request_factory.post('/')
#         request.user = self.user
#
#         data = {
#             'name': 'project',
#
#         }
#         serializer = ProjectSerializer(data={}, context={"request": request})
#         serializer.is_valid()
#
#         print(serializer.data, serializer.errors)

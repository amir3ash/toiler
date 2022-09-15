import datetime
from collections import defaultdict
from logging import Logger
from typing import List, Callable

from django.db import transaction
from django.db.models import Q, F, QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty
from rest_framework.serializers import as_serializer_error
from rest_framework.settings import api_settings
from rest_framework.utils import html
from rest_framework.validators import UniqueTogetherValidator

from chat.consumers import send_comment_to_channel
from gantt.models import Team, Role, TeamMember, Project, Task, \
    Activity, Assigned, State, Comment
from user.models import User
from user.serializers import UserSearchSerializer

from django.core.exceptions import ValidationError as DjangoValidationError

logger = Logger(__name__)


class FilteredRelatedField(serializers.PrimaryKeyRelatedField):

    def get_queryset(self):
        user = self.context['request'].user
        return self._get_queryset(user)

    def __init__(self, get_queryset: Callable[[User], QuerySet], **kwargs):
        self._get_queryset = get_queryset
        super().__init__(**kwargs)


class ProjectForeignKey(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return Project.objects.filter(project_manager=self.context['request'].user)


class StateSerializer(serializers.ModelSerializer):
    """ only allow project_manager to create."""
    project = ProjectForeignKey()

    class Meta:
        model = State
        fields = '__all__'


class StateUpdateSerializer(StateSerializer):
    """A `StateSerializer` with readonly project."""
    project = ProjectForeignKey(read_only=True)

    class Meta:
        model = State
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    """
    A Serializer that allow to create `Comment` on activities that current user is:
     **project_manager** or **team_member**.
    Sets `author` to current user.
     """

    class Meta:
        model = Comment
        fields = ('id', 'author', 'activity', 'created_at', 'updated_at', 'text')

    author = serializers.PrimaryKeyRelatedField(read_only=True)
    activity = FilteredRelatedField(
        lambda user: Activity.objects.filter(
            Q(task__project__project_manager=user) |
            Q(task__project__team__teammember__user=user)
        ).distinct()
    )

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        comment = Comment(**validated_data)
        comment.save()

        data = CommentVerboseSerializer(comment, read_only=True).data
        send_comment_to_channel(comment.id, data)

        return comment


class CommentOnlyChangeTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('id', 'author', 'activity', 'created_at', 'updated_at', 'text')
        read_only_fields = ('author', 'activity', 'updated_at', 'created_at')


class CommentVerboseSerializer(serializers.ModelSerializer):
    """A readonly serializer that returns `author` with structure of `UserSearchSerializer`."""
    author = UserSearchSerializer()

    class Meta:
        read_only = True
        model = Comment
        fields = ('id', 'author', 'activity', 'created_at', 'updated_at', 'text')
        read_only_fields = fields


class TeamSerializer(serializers.ModelSerializer):
    """ only allow project_manager to create."""
    project = ProjectForeignKey()

    class Meta:
        model = Team
        fields = '__all__'


class RoleSerializer(serializers.ModelSerializer):
    """ only allow project_manager to create."""

    project = FilteredRelatedField(lambda user: Project.objects.filter(project_manager=user))

    class Meta:
        model = Role
        fields = '__all__'


class TeamMemberSerializer(serializers.ModelSerializer):
    """
    A serializer thant allow project manager to create `TeamMember`.
    `team` and `role` must be in same project. `user` can be everybody.

    - A team could have only one user with selected role.

    *Everyone can be added to any project. so its dangerous.*
    """

    team = FilteredRelatedField(lambda user: Team.objects.filter(project__project_manager=user))
    role = FilteredRelatedField(lambda user: Role.objects.filter(project__project_manager=user))

    def validate(self, attrs):
        if attrs and attrs['team'].project.id == attrs['role'].project.id:
            return super().validate(attrs)
        raise serializers.ValidationError('projects not match.')

    class Meta:
        model = TeamMember
        fields = ('id', 'team', 'user', 'role')
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=['team', 'user']
            )
        ]


class TeamMemberGetSerializer(TeamMemberSerializer):
    """It allows to **modify** but with readonly `user`."""
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    def validate(self, attrs: dict):
        if attrs:
            instance = self.instance
            team_project_id = attrs['team'].project.id if attrs.get('team') else instance.team.project.id
            role_project_id = attrs['role'].project.id if attrs.get('role') else instance.role.project.id

            if team_project_id == role_project_id:
                return super(serializers.ModelSerializer, self).validate(attrs)

        raise serializers.ValidationError('projects not match.')


class VerboseTeamMemberSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)
    role = RoleSerializer(read_only=True)
    user = UserSearchSerializer(read_only=True)

    class Meta:
        model = TeamMember
        fields = ('id', 'team', 'role', 'user')
        read_only_fields = fields


# - - - -- - - - - - -- - - - -- - --- - -  - -- - -- - - -- - - --

class ProjectSerializer(serializers.ModelSerializer):
    """Creates `Project` and set current user as`project_manager`."""
    project_manager = serializers.PrimaryKeyRelatedField(read_only=True)

    def create(self, validated_data):
        validated_data['project_manager'] = self.context['request'].user
        project = Project(**validated_data)
        project.save()
        return project

    class Meta:
        model = Project
        fields = '__all__'
        # exclude = ('invitation_link_date',)


# - - - - - - - -  - - - - - - - -  - - - - - - - - - - - -

class CheckDatesMixin:
    def get_last_value(self, attrs: dict, key: str):
        value = attrs.get(key)
        if value:
            return value

        value = getattr(self.instance, key, None)
        if value:
            return value

        return None

    def validate(self, attrs: dict):
        errors = defaultdict(list)

        if attrs:
            now = datetime.datetime.now(tz=datetime.timezone.utc)

            planned_start_date = self.get_last_value(attrs, 'planned_start_date')
            planned_end_date = self.get_last_value(attrs, 'planned_end_date')
            actual_start_date = self.get_last_value(attrs, 'actual_start_date')
            actual_end_date = self.get_last_value(attrs, 'actual_end_date')

            if planned_start_date > planned_end_date:
                errors['planned_end_date'].append('planned_start_date should be before planned_end_date.')

            if actual_start_date and actual_end_date and actual_start_date > actual_end_date:
                errors['actual_end_date'].append('actual_start_date should be before actual_end_date.')

            if actual_start_date and actual_start_date > now:
                errors['actual_start_date'].append('actual_start_date should be before now.')

            if actual_end_date:
                if actual_end_date > now:
                    errors['actual_end_date'].append('actual_end_date should be before now.')
                if actual_start_date is None:
                    errors['actual_start_date'].append('actual_start_date must be not empty.')

        if errors:
            raise ValidationError(errors)

        return attrs


class TaskSerializer(CheckDatesMixin, serializers.ModelSerializer):
    """ only allow project_manager to create."""

    class ProjectRK(serializers.PrimaryKeyRelatedField):
        def get_queryset(self):
            return Project.objects.filter(project_manager=self.context['request'].user)

    project = ProjectRK()

    class Meta:
        model = Task
        fields = '__all__'


class TaskUpdateSerializer(TaskSerializer):
    """A serializer with readonly project."""
    project = serializers.PrimaryKeyRelatedField(read_only=True)


class AssignedListSerializer(serializers.ListSerializer):
    """A serializer to handle multiple `Assigned` when `many=True`."""

    def myfunc(self, data):
        pass

    def val(self, data):
        (is_empty_value, data) = self.validate_empty_values(data)
        if is_empty_value:
            return data

        value = self.child.to_internal_value(data)

        self.myfunc(value)
        return value

    def run_validation(self, data=empty):
        self.child.validators = []
        (is_empty_value, data) = self.validate_empty_values(data)
        if is_empty_value:
            return data

        # 000000

        if html.is_html_input(data):
            data = html.parse_html_list(data, default=[])

        if not isinstance(data, list):
            message = self.error_messages['not_a_list'].format(
                input_type=type(data).__name__
            )
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: [message]
            }, code='not_a_list')

        if not self.allow_empty and len(data) == 0:
            message = self.error_messages['empty']
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: [message]
            }, code='empty')

        if self.max_length is not None and len(data) > self.max_length:
            message = self.error_messages['max_length'].format(max_length=self.max_length)
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: [message]
            }, code='max_length')

        if self.min_length is not None and len(data) < self.min_length:
            message = self.error_messages['min_length'].format(min_length=self.min_length)
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: [message]
            }, code='min_length')

        ret = []
        errors = []

        for item in data:
            try:
                validated = self.val(item)

            except ValidationError as exc:
                errors.append(exc.detail)
            else:
                ret.append(validated)
                errors.append({})

        # 0000000
        value = self.to_internal_value(data)
        try:
            self.run_validators(value)
            value = self.validate(value)
            assert value is not None, '.validate() should return the validated data'
        except (ValidationError, DjangoValidationError) as exc:
            raise ValidationError(detail=as_serializer_error(exc))

        return super().run_validation(data)


class Aau(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return Activity.objects.filter(task__project__project_manager=self.context['request'].user)


class AssignedSerializer(serializers.ModelSerializer):
    """ only allow project_manager to create. Doesn't modify activity when updating` """

    user = FilteredRelatedField(lambda user: User.objects.filter(
        teammember__team__project__project_manager=user).distinct())
    activity = Aau()

    def __init__(self, *args, **kwargs):
        """If object is being updated don't allow to be changed."""
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields.get('activity').read_only = True

    class Meta:
        model = Assigned
        list_serializer_class = AssignedListSerializer
        fields = ('id', 'user', 'activity')
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=['user', 'activity']
            )
        ]


class AssignedUpdateSerializer(AssignedSerializer):
    """A Serializer with readonly `activity` that allows `many=True` """
    activity = Aau(read_only=True)

    class Meta:
        model = Assigned
        fields = ('id', 'user', 'activity')
        list_serializer_class = AssignedListSerializer
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=['user', 'activity']
            )
        ]


class VerboseAssignedSerializer(serializers.ModelSerializer):
    """Readonly serializer with verbose `user` """
    user = serializers.SerializerMethodField()

    @swagger_serializer_method(serializer_or_field=UserSearchSerializer)
    def get_user(self, obj: Assigned):
        return UserSearchSerializer(obj.user, read_only=True).data

    class Meta:
        read_only = True
        model = Assigned
        fields = ('id', 'user', 'activity')
        read_only_fields = fields


class VerboseActivity(serializers.ModelSerializer):
    """
    A Serializer with verbose `state` and `assignees`.
    `assignees` is list of `Assigned` model with `VerboseAssignedSerializer` serializer.
    """
    state = serializers.SerializerMethodField()
    assignees = serializers.SerializerMethodField(source='assigned_set')

    @swagger_serializer_method(serializer_or_field=StateSerializer)
    def get_state(self, obj: Activity) -> StateSerializer:
        return StateSerializer(obj.state, read_only=True).data

    @swagger_serializer_method(serializer_or_field=VerboseAssignedSerializer(many=True))
    def get_assignees(self, obj: Activity):
        assignees = obj.assigned_set.all()
        return VerboseAssignedSerializer(assignees, many=True, read_only=True).data

    class Meta:
        model = Activity
        fields = ['id', 'name', 'task', 'description', 'planned_start_date', 'planned_end_date',
                  'planned_budget', 'actual_start_date', 'actual_end_date', 'actual_budget', 'dependency', 'state',
                  'assignees'
                  ]


class ActivitySerializer(CheckDatesMixin, serializers.ModelSerializer):
    """
    It allows project_manager or team_member to create, with list of user_ids as assignees.

    The `task` field is readonly when updating.

    When the user modify the assignees, it creates or deletes `Assigned` objects according to user ids.
    """

    class DependencyRK(serializers.PrimaryKeyRelatedField):
        def get_queryset(self):
            user = self.context['request'].user
            instance = self.parent.instance
            instance_id = instance if instance is None else instance.id

            return Activity.objects.filter(
                Q(task__project__project_manager=user) |
                Q(task__project__team__teammember__user=user)
            ).only('id', 'name').exclude(id=instance_id).distinct()

    task = FilteredRelatedField(lambda user: Task.objects.filter(
        Q(project__project_manager=user) |
        Q(project__team__teammember__user=user)).distinct())

    state = FilteredRelatedField(lambda user: State.objects.filter(
        Q(project__team__teammember__user=user) |
        Q(project__project_manager=user)
    ).distinct(), required=False, allow_null=True)

    dependency = DependencyRK(required=False, allow_null=True)

    assignees = AssignedUpdateSerializer(required=False, many=True, source='assigned_set')

    def validate(self, attrs: dict):

        if attrs:
            instance = self.instance
            task_project_id = attrs['task'].project.id if attrs.get('task') else instance.task.project.id
            state_project_id = None
            dependency_project_id = None

            if instance:
                if instance.state:
                    state_project_id = instance.state.project.id

                if instance.dependency:
                    dependency_project_id = instance.dependency.task.project.id

            state_project_id = attrs['state'].project.id if attrs.get('state') else state_project_id
            dependency_project_id = attrs['dependency'].task.project.id if attrs.get('dependency')\
                                    else dependency_project_id

            if (task_project_id == state_project_id or state_project_id is None) \
                    and (task_project_id == dependency_project_id or dependency_project_id is None):
                return super().validate(attrs)

        raise serializers.ValidationError('projects not match.')

    def __init__(self, *args, **kwargs):
        """If object is being updated don't allow to be changed."""
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields.get('task').read_only = True

    def update(self, instance, validated_data):
        assigned_set = validated_data.pop('assigned_set', None)

        if assigned_set is not None:

            # all users that requested to assigned
            input_user_ids = {pk['user'].id for pk in assigned_set}

            # all users who this activity assigned to them
            activity_assignees = set(item for item in instance.assigned_set.values_list('user_id', flat=True))

            assigned_users_for_delete = activity_assignees - input_user_ids
            new_assigned_users = input_user_ids - activity_assignees

            new_assigned = [Assigned(user_id=user_id, activity_id=instance.id) for user_id in new_assigned_users]

            try:
                with transaction.atomic():
                    Assigned.objects.filter(user_id__in=assigned_users_for_delete).delete()
                    Assigned.objects.bulk_create(new_assigned)
            except Exception as e:
                logger.error(e)
                raise ValidationError

        return super().update(instance, validated_data)

    def create(self, validated_data):
        assigned_set = validated_data.pop('assigned_set', None)

        activity = super(ActivitySerializer, self).create(validated_data)

        if assigned_set is None:
            return activity

        input_user_ids = {pk['user'].id for pk in assigned_set}
        new_assigned = [Assigned(user_id=user_id, activity_id=activity.id) for user_id in input_user_ids]

        Assigned.objects.bulk_create(new_assigned)

        return activity

    class Meta:
        model = Activity
        fields = ['id', 'name', 'task', 'description', 'planned_start_date', 'planned_end_date',
                  'planned_budget', 'actual_start_date', 'actual_end_date', 'actual_budget', 'dependency', 'state',
                  'assignees'
                  ]


class ActivityUpdateSerializer(ActivitySerializer):
    """A serializer with readonly `task`."""
    task = serializers.PrimaryKeyRelatedField(read_only=True)


class AssignedToMeSerializer(serializers.ModelSerializer):
    """A serializer with project name as `project`."""
    project = serializers.SerializerMethodField()
    project_id = serializers.SerializerMethodField()

    def get_project(self, obj) -> str:
        return obj.task.project.name

    def get_project_id(self, obj) -> int:
        return obj.task.project_id

    class Meta:
        model = Activity
        fields = ['id', 'name', 'task', 'planned_end_date',
                  'actual_start_date', 'dependency', 'state', 'project', 'project_id']


class TaskWithActivitiesSerializer(serializers.ModelSerializer):
    activities = serializers.SerializerMethodField()
    limit = 10

    class Meta:
        model = Task
        # order = 'planned'
        fields = ['id', 'name', 'planned_start_date', 'planned_end_date', 'actual_start_date', 'actual_end_date',
                  'description', 'planned_budget', 'actual_budget', 'activities']

    @swagger_serializer_method(serializer_or_field=VerboseActivity(many=True))
    def get_activities(self, obj: Task):
        activities = obj.activity_set.all()[:self.limit]
        return VerboseActivity(activities, many=True, read_only=True).data


class ProjectWithRelatedSerializer(serializers.ModelSerializer):
    tasks = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'planned_start_date', 'planned_end_date', 'actual_start_date', 'actual_end_date',
                  'description', 'tasks']

    @swagger_serializer_method(serializer_or_field=TaskWithActivitiesSerializer(many=True))
    def get_tasks(self, obj: Project):
        tasks = obj.task_set.all()
        return TaskWithActivitiesSerializer(tasks, many=True, read_only=True).data


class ProjectSimpleVerboseSerializer:
    def __init__(self, instance: Project):
        self.instance = instance

    def _get_activity(self, activity: Activity):
        data: dict = {
            'id': activity.id, 'name': activity.name, 'task': activity.task_id, 'description': activity.description,
            'planned_start_date': activity.planned_start_date, 'planned_end_date': activity.planned_end_date,
            'planned_budget': activity.planned_budget, 'actual_start_date': activity.actual_start_date,
            'actual_end_date': activity.actual_end_date, 'actual_budget': activity.actual_budget,
            'dependency': activity.dependency_id, 'state': activity.state_id
        }
        return data

    def _get_task(self, task: Task):
        data = {
            'id': task.id, 'name': task.name, 'planned_start_date': task.planned_start_date,
            'planned_end_date': task.planned_end_date, 'actual_start_date': task.actual_start_date,
            'actual_end_date': task.actual_end_date, 'description': task.description,
            'planned_budget': task.planned_budget, 'actual_budget': task.actual_budget,
            'activities': [self._get_activity(activity) for activity in task.activity_set.all()]
        }
        return data

    def _get_user(self):
        pass

    def get_data(self):
        project = self.instance
        data = {
            'id': project.id,
            'name': project.name,
            'project_manager': project.project_manager_id,
            'planned_start_date': project.planned_start_date,
            'planned_end_date': project.planned_end_date,
            'actual_start_date': project.actual_start_date,
            'actual_end_date': project.actual_end_date,
            'description': project.description,
            'tasks': [self._get_task(task) for task in project.task_set.all()]
        }
        return data

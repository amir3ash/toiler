from functools import wraps

import django_filters
from django.core.cache import cache
from django.db.models import Prefetch, Window
from django.db.models.functions import RowNumber
from django.utils.decorators import method_decorator
from django.utils.timezone import make_aware
from django_cte import With
from django_filters.rest_framework import FilterSet
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, mixins, views
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from gantt.models import ChertActivity
from gantt.permissons import IsProjectManagerOrReadOnly, IsProjectManagerOrReadOnlyComment
from gantt.serializers import *
from gantt.notifier import BulkNotify
from gantt.tests.base import Timer

timer = Timer()
logger = Logger(__name__)


def set_update_schema(serializer, names: iter = ('update', 'partial_update')):
    """
    Set swagger responses schema for every method names.
    """

    def wrapper(view):
        for name in names:
            decorator = swagger_auto_schema(request_body=serializer)
            view = method_decorator(decorator, name)(view)

        return view

    return wrapper


class StateViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsProjectManagerOrReadOnly]

    def get_queryset(self):
        return State.objects.filter(
            Q(project__team__teammember__user=self.request.user) |
            Q(project__project_manager=self.request.user)
        ).distinct()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StateSerializer

        return StateUpdateSerializer


class StateListView(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = StateSerializer

    def get_queryset(self):
        project_pk = self.kwargs.get('proj_pk')
        if project_exists(project_pk, self.request.user):
            return State.objects.filter(project_id=project_pk)


class CommentListView(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = CommentVerboseSerializer

    def get_queryset(self):
        activity_pk = self.kwargs.get('activity_pk')
        user = self.request.user

        if Activity.objects.filter(
                Q(task__project__project_manager=user) |
                Q(task__project__team__teammember__user=user),
                id=activity_pk
        ).exists():
            return Comment.objects.filter(activity_id=activity_pk)


class CommentDetailView(mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsProjectManagerOrReadOnlyComment]

    def get_queryset(self):
        return Comment.objects.filter(
            Q(activity__task__project__team__teammember__user=self.request.user) |
            Q(activity__task__project__project_manager=self.request.user)
        ).distinct()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommentSerializer
        else:
            return CommentOnlyChangeTextSerializer


class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ('project',)  # TODO write tests

    def get_queryset(self):
        return Team.objects.filter(project__project_manager=self.request.user)
    # todo only project manager can create or modify the one


class RoleViewSet(viewsets.ModelViewSet):
    serializer_class = RoleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ('project',)

    def get_queryset(self):
        return Role.objects.filter(project__project_manager=self.request.user)


class TeamMemberGenericView(viewsets.GenericViewSet):

    def get_queryset(self):
        return TeamMember.objects.filter(team__project__project_manager=self.request.user)


def verbose_list(related: iter, serializer):
    """
    when calling list method, If query_params contains the key 'verbose' with value 'true',
    it changes serializer
    """

    def wrapper(view):
        old_list = view.list

        @wraps(view.list)
        def func(self, request, *args, **kwargs):
            if self.request.query_params.get('verbose') == 'true':
                queryset = self.get_queryset().prefetch_related(*related)
                self.get_serializer = serializer

                def get_queryset():
                    return queryset

                self.get_queryset = get_queryset

            return old_list(self, request, *args, **kwargs)

        view.list = func
        return view

    return wrapper


class TeamProjectFilter(FilterSet):
    project = django_filters.ModelChoiceFilter(field_name="team__project",
                                               queryset=Project.objects.all())

    class Meta:
        model = TeamMember
        fields = ('project', 'team')


@verbose_list(('team', 'role', 'user'), VerboseTeamMemberSerializer)
class TeamMemberList(mixins.CreateModelMixin, mixins.ListModelMixin, TeamMemberGenericView):
    serializer_class = TeamMemberSerializer
    filter_backends = [DjangoFilterBackend]
    # filterset_fields = ('team__id',)
    filter_class = TeamProjectFilter  # TODO write tests


class TeamMemberDetail(mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       mixins.DestroyModelMixin,
                       # mixins.ListModelMixin,
                       TeamMemberGenericView):
    serializer_class = TeamMemberGetSerializer


class EmployeesListView(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = UserSearchSerializer

    def get_queryset(self):
        project_pk = self.kwargs.get('proj_pk')
        if project_exists(project_pk, self.request.user):
            return User.objects.filter(teammember__team__project_id=project_pk).distinct()


# - - - - - - - - - - - - - - - - - - - - -- -

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return Project.objects.filter(project_manager=self.request.user)


# - - -  - - -- - - - - - - -- - - - - - -- - - - - -
def project_exists(project_pk, user) -> bool:
    """ :returns True if user is project_manager or a team_member of the project, else False"""
    return Project.objects.filter(
        Q(project_manager=user) | Q(team__teammember__user=user), id=project_pk
    ).exists()


class TaskGenericView(viewsets.GenericViewSet):
    def get_queryset(self):
        return Task.objects.filter(project__project_manager=self.request.user)


class TaskListView(mixins.ListModelMixin, TaskGenericView):
    serializer_class = TaskSerializer

    def get_queryset(self):
        """
        if project has been created by project manager
        or project has been under process by employee
        """
        project_pk = self.kwargs.get('proj_pk')
        if project_exists(project_pk, self.request.user):
            return Task.objects.filter(project_id=project_pk)


class TaskUpdateView(mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     TaskGenericView):
    permission_classes = [IsAuthenticated, IsProjectManagerOrReadOnly]  # Todo it can be with roles or teams
    serializer_class = TaskUpdateSerializer

    def get_queryset(self):
        return Task.objects.filter(
            Q(project__project_manager=self.request.user) |
            Q(project__team__teammember__user=self.request.user)).distinct()  # todo change `distinct`


class TaskCreateView(mixins.CreateModelMixin, TaskGenericView):
    serializer_class = TaskSerializer


@verbose_list(('state', 'assigned_set__user'), VerboseActivity)
class ActivityListView(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ActivitySerializer

    def get_queryset(self):
        project_pk = self.kwargs.get('proj_pk')
        if project_exists(project_pk, self.request.user):
            return Activity.objects.filter(task__project_id=project_pk)


@set_update_schema(ActivityUpdateSerializer())
class ActivityViewSet(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.DestroyModelMixin,
                      viewsets.GenericViewSet):
    serializer_class = ActivitySerializer

    def get_queryset(self):
        return Activity.objects.filter(
            Q(task__project__project_manager=self.request.user) |
            Q(task__project__team__teammember__user=self.request.user)).distinct()


@set_update_schema(AssignedUpdateSerializer)
class AssignedCreateView(mixins.CreateModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.DestroyModelMixin,
                         viewsets.GenericViewSet):
    serializer_class = AssignedSerializer

    def get_queryset(self):
        user = self.request.user
        return Assigned.objects.filter(
            user__teammember__team__project__project_manager=user
        ).distinct()


@verbose_list(('user',), VerboseAssignedSerializer)
class AssignedListView(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = AssignedSerializer

    def get_queryset(self):
        project_pk = self.kwargs.get('proj_pk')
        if project_exists(project_pk, self.request.user):
            return Assigned.objects.filter(activity__task__project__id=project_pk)


class AssignedToMeListView(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = AssignedToMeSerializer

    def get_queryset(self):
        return Activity.objects.filter(assigned__user=self.request.user, actual_end_date__isnull=True)


class GetAll(views.APIView):
    serializer_class = ProjectWithRelatedSerializer  # ProjectSimpleVerboseSerializer
    limit = TaskWithActivitiesSerializer.limit
    cache_pre_key = 'activities_in_project_{:d}'

    @swagger_auto_schema(responses={200: ProjectWithRelatedSerializer()})
    def get(self, request, pk):
        project_pk = pk
        if project_exists(project_pk, self.request.user):

            activities = self.get_activity_ids(project_pk)

            project = Project.objects.filter(id=project_pk). \
                prefetch_related(
                'task_set',
                Prefetch('task_set__activity_set', Activity.objects.filter(id__in=activities)),
                'task_set__activity_set__assigned_set',
                'task_set__activity_set__assigned_set__user',
                'task_set__activity_set__state'
            ).first()
            if project:
                data = self.serializer_class(project).data
                return Response(data)

        return Response({})

    def get_activity_ids(self, project_id):
        cache_key = self.cache_pre_key.format(project_id)
        result = cache.get(cache_key)
        if result:
            return result

        cte = With(
            ChertActivity.objects.filter(task__project_id=project_id)
                .annotate(
                row_number=Window(
                    expression=RowNumber(),
                    partition_by=[F('task_id')],
                    # order_by=F('planed_start_date').asc()
                )
            ).only('id', 'task_id')
        )
        result = tuple(
            cte.queryset().with_cte(cte).filter(row_number__lte=self.limit).values_list('id', flat=True)
        )

        cache.set(cache_key, result)
        return result


class AutoSchedule(views.APIView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.activity_map = dict()
        self.task_map = dict()

    def put(self, request, pk):
        project_pk = pk
        project = get_object_or_404(Project.objects.filter(id=project_pk, project_manager=request.user))

        activities: 'QuerySet[Activity]' = Activity.objects.filter(task__project_id=project_pk)
        tasks = Task.objects.filter(project_id=project_pk)

        for activity in activities:
            self.activity_map[activity.id] = activity

        day_zero = make_aware(datetime.datetime.utcfromtimestamp(0))
        day_infinity = make_aware(datetime.datetime.today() + datetime.timedelta(weeks=1000))
        for task in tasks:
            task.planned_start_date = day_infinity
            task.planned_end_date = day_zero
            self.task_map[task.id] = task

        activity_list = self._topological_sort(activities)
        self._early_path(project, activity_list)

        return Response({})

    def _early_path(self, project, activities):
        project_start_date = datetime.datetime.fromordinal(project.planned_start_date.toordinal())
        project_end_date = datetime.datetime.fromordinal(project.planned_end_date.toordinal())
        project_start_date = make_aware(project_start_date)
        project_end_date = make_aware(project_end_date)

        for i in range(len(activities)):
            activity = activities[i]
            duration = activity.planned_end_date - activity.planned_start_date

            activity_early_start = project_start_date
            activity_early_final = project_start_date + duration

            if activity.dependency_id:
                d_ef = self.activity_map[activity.dependency_id].early_final
                activity_early_start = d_ef
                activity_early_final = d_ef + duration

            activity.early_final = activity_early_final
            activity.planned_start_date = activity_early_start
            activity.planned_end_date = activity_early_final

            task = self.task_map[activity.task_id]
            task.planned_start_date = min(max(project_start_date, activity_early_start), task.planned_start_date)
            task.planned_end_date = max(min(project_end_date, activity_early_final), task.planned_end_date)

        tasks = self.task_map.values()
        Task.objects.bulk_update(tasks, fields=['planned_start_date', 'planned_end_date'])
        Activity.objects.bulk_update(activities, fields=['planned_start_date', 'planned_end_date'])

        self._notify_tasks_updated(tasks)
        self._notify_activities_updated(activities)

    def _topological_sort(self, activities):
        stack = []
        visited = set()

        def traverse(activity):
            if activity.id in visited:
                return

            if activity.dependency_id:
                depend_activity = self.activity_map[activity.dependency_id]
                traverse(depend_activity)

            stack.append(activity)
            visited.add(activity.id)

        for act in activities:
            traverse(act)

        return stack

    @staticmethod
    def _notify_activities_updated(activities):
        with BulkNotify('updated', 'activity') as b:
            for activity in activities:
                b.notify(activity.id, activity.task_id)

    @staticmethod
    def _notify_tasks_updated(tasks):
        with BulkNotify('updated', 'task') as b:
            for task in tasks:
                b.notify(task.id, task.project_id)
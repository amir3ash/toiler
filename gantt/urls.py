from django.urls import path, include
from rest_framework import routers

from gantt import views

router = routers.DefaultRouter()

router.register(r'team', views.TeamViewSet, basename='team')
router.register(r'role', views.RoleViewSet, basename='role')
router.register(r'team-member', views.TeamMemberList, basename='team-member')
router.register(r'team-member', views.TeamMemberDetail, basename='team-member')
router.register(r'(?P<proj_pk>[0-9]+)/employee', views.EmployeesListView, basename='employee')

router.register(r'comment', views.CommentDetailView, basename='comment')
router.register(r'(?P<activity_pk>[0-9]+)/comment', views.CommentListView, basename='comment')
router.register(r'state', views.StateViewSet, basename='state')
router.register(r'(?P<proj_pk>[0-9]+)/state', views.StateListView, basename='state')

router.register(r'project', views.ProjectViewSet, basename='project')

router.register(r'(?P<proj_pk>[0-9]+)/task', views.TaskListView, basename='task')
router.register(r'task', views.TaskUpdateView, basename='task')
router.register(r'task', views.TaskCreateView, basename='task')

router.register(r'(?P<proj_pk>[0-9]+)/activity', views.ActivityListView, basename='activity')
router.register(r'activity', views.ActivityViewSet, basename='activity')
router.register(r'(?P<proj_pk>[0-9]+)/assigned', views.AssignedListView, basename='assigned')
router.register(r'assigned', views.AssignedCreateView, basename='assigned')
router.register(r'assigned_to_me', views.AssignedToMeListView, basename='assigned_to_me')

app_name = 'gantt'

urlpatterns = [
    path('', include(router.urls)),
    path('all/<int:pk>/', views.GetAll.as_view(), name='get_project_w_related'),
    path('auto-schedule/<int:pk>/', views.AutoSchedule.as_view(), name="auto_schedule")
]

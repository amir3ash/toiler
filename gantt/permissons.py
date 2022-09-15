from rest_framework.permissions import BasePermission, SAFE_METHODS

from gantt.models import Project


class IsProjectManagerOrReadOnly(BasePermission):
    """
    Object-level permission to only allow ProjectManager of a Task to edit it.
    """

    def has_object_permission(self, request, view, instance):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True

        return Project.objects.filter(id=instance.project.id, project_manager=request.user).exists()


class IsProjectManagerOrReadOnlyComment(BasePermission):
    """
    Object-level permission to only allow ProjectManager to edit it.
    """

    def has_object_permission(self, request, view, comment):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True

        return Project.objects.filter(id=comment.activity.task.project.id, project_manager=request.user).exists()

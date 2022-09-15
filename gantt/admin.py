from django.contrib import admin
from gantt.models import Task, Project, Activity, Team, TeamMember

admin.site.register(Task)
admin.site.register(Project)
admin.site.register(Activity)
admin.site.register(Team)
admin.site.register(TeamMember)

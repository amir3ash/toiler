from django.db import models
from django_cte import CTEManager

from user.models import User


class TimeStampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Project(models.Model):
    name = models.CharField(max_length=90)
    planned_start_date = models.DateField()
    planned_end_date = models.DateField()
    actual_start_date = models.DateField(blank=True, null=True)
    actual_end_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True)
    project_manager = models.ForeignKey(User, on_delete=models.CASCADE, null=False)

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=90)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False)

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=90)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False)

    def __str__(self):
        return self.name


class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['team', 'user'], name='unique_team_employee')]


class State(models.Model):
    name = models.CharField(max_length=50)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.project.id if self.project else ':::'}: {self.name}"


# -  - - -- -  - - - - - - -- - - - - - -- - - -- - --

class Task(models.Model):
    name = models.CharField(max_length=90)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    planned_start_date = models.DateTimeField()
    planned_end_date = models.DateTimeField()
    planned_budget = models.DecimalField(decimal_places=2, max_digits=8, default=0)
    actual_start_date = models.DateTimeField(null=True)
    actual_end_date = models.DateTimeField(null=True)
    actual_budget = models.DecimalField(decimal_places=2, max_digits=8, default=0)
    description = models.TextField(blank=True)

    def __str__(self):
        return f'{self.name} on {self.project}'


class Activity(models.Model):
    name = models.CharField(max_length=90)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    planned_start_date = models.DateTimeField()
    planned_end_date = models.DateTimeField()
    planned_budget = models.DecimalField(decimal_places=2, max_digits=8, null=True)  # this changed
    actual_start_date = models.DateTimeField(null=True)
    actual_end_date = models.DateTimeField(null=True)
    actual_budget = models.DecimalField(decimal_places=2, max_digits=8, null=True)
    dependency = models.ForeignKey('self', default=None, null=True, on_delete=models.CASCADE)
    state = models.ForeignKey(State, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f'{self.name} in {self.task}'


class ChertActivity(Activity):
    class Meta:
        proxy = True

    objects = CTEManager()


class Assigned(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['activity', 'user'], name='unique_activity_user')]

    def __str__(self):
        return f'"{self.user}"'  # on activity "{self.activity}"'


class Comment(TimeStampMixin, models.Model):
    text = models.TextField(max_length=200)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)

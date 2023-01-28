from json import dumps as json_dumps
from logging import getLogger
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
import redis
from .models import Project, Activity, Task, State
from .serializers import ActivitySerializer, TaskSerializer, ProjectSerializer, StateSerializer
from .views import GetAll

logger = getLogger(__name__)
cache_str = GetAll.cache_pre_key

del GetAll

red = redis.StrictRedis(host='127.0.0.1', port=6379)

_EVENTS = {"added", "updated", "deleted"}


def notify(event: str, obj_type: str, data: dict):
    """
    publish event to **"changes"** redis channel.

    :param event: "added" or "updated" or "deleted"
    :param obj_type:
    :param data: serialization of object
    :return: None
    """
    if event not in _EVENTS:
        raise Exception(f"event not in {_EVENTS}")

    data_capsule = {
        "event": event,
        "type": obj_type,
        "id": data["id"],
        "obj": data
    }

    str_json = json_dumps(data_capsule)
    red.publish('changes', str_json)


def delete_cache(activity_id):
    pid = Project.objects.filter(task__activity__id=activity_id).values_list('id', flat=True)[:1]
    if pid:
        project_id = pid[0]
        cache_key = cache_str.format(project_id)
        r = cache.delete(cache_key)
        if r:
            logger.info(f'cache "{cache_key}" deleted.')


@receiver(post_delete, sender=Activity, dispatch_uid='activity_deleted')
def activity_post_delete_handler(instance: Activity, **kwargs):
    delete_cache(instance.id)

    data = ActivitySerializer(instance).data
    notify("deleted", "activity", data)


@receiver(post_save, sender=Activity, dispatch_uid='activity_updated')
def activity_post_save_handler(instance: Activity, created, **kwargs):
    if created:
        delete_cache(instance.id)

    data = ActivitySerializer(instance).data
    notify("added" if created else "updated", "activity", data)


@receiver(post_delete, sender=Task, dispatch_uid='task_deleted')
def task_post_delete_handler(instance: Task, **kwargs):
    data = TaskSerializer(instance).data
    notify("deleted", "task", data)


@receiver(post_save, sender=Task, dispatch_uid='task_updated')
def task_post_save_handler(instance: Task, created, **kwargs):
    data = TaskSerializer(instance).data
    notify("added" if created else "updated", "task", data)


@receiver(post_delete, sender=Project, dispatch_uid='project_deleted')
def project_post_delete_handler(instance: Project, **kwargs):
    data = ProjectSerializer(instance).data
    notify("deleted", "project", data)


@receiver(post_save, sender=Project, dispatch_uid='project_updated')
def project_post_save_handler(instance: Project, created, **kwargs):
    data = ProjectSerializer(instance).data
    notify("added" if created else "updated", "project", data)


@receiver(post_delete, sender=State, dispatch_uid='state_deleted')
def state_post_delete_handler(instance: State, **kwargs):
    data = StateSerializer(instance).data
    notify("deleted", "state", data)


@receiver(post_save, sender=Project, dispatch_uid='project_updated')
def state_post_save_handler(instance: State, created, **kwargs):
    data = StateSerializer(instance).data
    notify("added" if created else "updated", "state", data)

from json import dumps as json_dumps
from logging import getLogger
from typing import Type, Union

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from redis import StrictRedis
from .models import Project, Activity, Task, State, Assigned
from .views import GetAll

logger = getLogger(__name__)
cache_str = GetAll.cache_pre_key

del GetAll

red = StrictRedis(host='127.0.0.1', port=6379)

_EVENTS = {"added", "updated", "deleted"}


def notify(event: str, obj_type: str, object_id: int, parent_id: Union[int, Type[int]]):
    """
    publish event to **"changes"** redis channel.

    :param parent_id:
    :param object_id:
    :param event: "added" or "updated" or "deleted"
    :param obj_type:
    :return: None
    """
    if event not in _EVENTS:
        raise Exception(f"event not in {_EVENTS}")

    data_capsule = {
        "event": event,
        "type": obj_type,
        "id": object_id,
        "parent": parent_id
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

    notify("deleted", "activity", instance.id, instance.task_id)


@receiver(post_save, sender=Activity, dispatch_uid='activity_updated')
def activity_post_save_handler(instance: Activity, created, **kwargs):
    if created:
        delete_cache(instance.id)

    notify("added" if created else "updated", "activity", instance.id, instance.task_id)


@receiver(post_delete, sender=Task, dispatch_uid='task_deleted')
def task_post_delete_handler(instance: Task, **kwargs):
    notify("deleted", "task", instance.id, instance.project_id)


@receiver(post_save, sender=Task, dispatch_uid='task_updated')
def task_post_save_handler(instance: Task, created, **kwargs):
    notify("added" if created else "updated", "task", instance.id, instance.project_id)


@receiver(post_delete, sender=Project, dispatch_uid='project_deleted')
def project_post_delete_handler(instance: Project, **kwargs):
    notify("deleted", "project", instance.id, instance.project_manager_id)


@receiver(post_save, sender=Project, dispatch_uid='project_updated')
def project_post_save_handler(instance: Project, created, **kwargs):
    notify("added" if created else "updated", "project", instance.id, instance.project_manager_id)


@receiver(post_delete, sender=State, dispatch_uid='state_deleted')
def state_post_delete_handler(instance: State, **kwargs):
    notify("deleted", "state", instance.id, instance.project_id)


@receiver(post_save, sender=State, dispatch_uid='state_updated')
def state_post_save_handler(instance: State, created, **kwargs):
    notify("added" if created else "updated", "state", instance.id, instance.project_id)


@receiver(post_delete, sender=Assigned, dispatch_uid='assigned_deleted')
def assigned_post_delete_handler(instance: Assigned, **kwargs):
    notify("deleted", "assigned", instance.id, instance.activity_id)


@receiver(post_save, sender=Assigned, dispatch_uid='assigned_updated')
def state_post_save_handler(instance: Assigned, created, **kwargs):
    notify("added" if created else "updated", "assigned", instance.id, instance.activity_id)

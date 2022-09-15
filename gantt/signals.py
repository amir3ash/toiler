from logging import getLogger
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Project, Activity
from .views import GetAll

logger = getLogger(__name__)
cache_str = GetAll.cache_pre_key

del GetAll


def delete_cache(activity_id):
    pid = Project.objects.filter(task__activity__id=activity_id).values_list('id', flat=True)[:1]
    if pid:
        project_id = pid[0]
        cache_key = cache_str.format(project_id)
        r = cache.delete(cache_key)
        if r:
            logger.info(f'cache "{cache_key}" deleted.')


@receiver(post_delete, sender=Activity, dispatch_uid='activity_deleted')
def activity_post_delete_handler(instance, **kwargs):
    delete_cache(instance.id)


@receiver(post_save, sender=Activity, dispatch_uid='activity_updated')
def activity_post_save_handler(instance, created, **kwargs):
    if created:
        delete_cache(instance.id)

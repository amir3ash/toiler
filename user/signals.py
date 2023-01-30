from logging import getLogger
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from gantt.signals import notify
from .models import User

logger = getLogger(__name__)


@receiver(post_delete, sender=User, dispatch_uid='user_deleted')
def activity_post_delete_handler(instance: User, **kwargs):
    notify("deleted", "user", instance.id, 0)


@receiver(post_save, sender=User, dispatch_uid='user_updated')
def activity_post_save_handler(instance: User, created, **kwargs):
    notify("added" if created else "updated", "user", instance.id, 0)

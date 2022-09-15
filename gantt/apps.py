from django.apps import AppConfig


class GanttConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gantt'

    def ready(self):
        import gantt.signals

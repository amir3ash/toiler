from django.apps import AppConfig


class MyappConfig(AppConfig):
    name = 'user'

    def ready(self):
        import user.signals
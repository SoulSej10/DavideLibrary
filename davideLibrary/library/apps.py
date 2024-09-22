# from django.apps import AppConfig


# class LibraryConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'library'
from django.apps import AppConfig
from django.db.models.signals import post_migrate

class LibraryConfig(AppConfig):
    name = 'library'

    def ready(self):
        from .signals import create_user_groups
        post_migrate.connect(create_user_groups, sender=self)

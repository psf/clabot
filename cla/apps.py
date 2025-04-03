from django.apps import AppConfig


class ClaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cla"

    def ready(self):
        from . import events  # noqa: F401

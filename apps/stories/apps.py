from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class StoriesConfig(AppConfig):
    name = "apps.stories"
    verbose_name = _("stories")

    # def ready(self):
    #     try:
    #         import apps.user_account.signals  # noqa: F401
    #     except ImportError:
    #         pass

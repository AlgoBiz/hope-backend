from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PaymentsConfig(AppConfig):
    name = "apps.payments"
    verbose_name = _("payments")

    # def ready(self):
    #     try:
    #         import apps.user_account.signals  # noqa: F401
    #     except ImportError:
    #         pass

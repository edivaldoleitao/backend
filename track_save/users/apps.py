import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "track_save.users"
    verbose_name = _("Users")

    def ready(self):
        with contextlib.suppress(ImportError):
            import track_save.users.signals  # noqa: F401

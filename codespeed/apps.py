from django.apps import AppConfig
from django.conf import settings


class CodespeedConfig(AppConfig):
    name = 'codespeed'

    def ready(self):
        import warnings
        if settings.ALLOW_ANONYMOUS_POST:
            warnings.warn("Results can be posted by unregistered users")
            warnings.warn(
                "In the future anonymous posting will be disabled by default",
                category=FutureWarning)
        elif not settings.REQUIRE_SECURE_AUTH:
            warnings.warn(
                "REQUIRE_SECURE_AUTH is not True. This server may prompt for"
                " user credentials to be submitted in plaintext")

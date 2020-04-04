from django.apps import AppConfig


class NoicdepotConfig(AppConfig):
    name = 'noicDepot'

    def ready(self):
        import noicDepot.signals


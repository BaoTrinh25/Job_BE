# apps.py
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = 'jobs'

    def ready(self):
        import jobs.signals

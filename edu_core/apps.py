# Portfolio\Education_Villa\edu_core\apps.py

from django.apps import AppConfig


class EduCoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'edu_core'

    def ready(self):
        import edu_core.signals  # This ensures signals are loaded

        
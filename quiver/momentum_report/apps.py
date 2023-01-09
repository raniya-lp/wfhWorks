from django.apps import AppConfig


class MomentumReportConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'momentum_report'
    
    def ready(self):
        from . import time_set
        time_set.start()
        
from django.apps import AppConfig


class QueueSiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'queue_site'

    def ready(self):
        # Импортируем сигналы
        from . import signals
        # Вызываем инициализацию для существующих пользователей
        signals.initialize_user_lab_progress()
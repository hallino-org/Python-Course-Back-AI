from django.apps import AppConfig


class QuestionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "questions"
    verbose_name = "Questions"

    def ready(self):
        import questions.models  # import models to register signals

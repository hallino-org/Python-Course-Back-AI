from django.urls import path

from . import views  # Uncommented

app_name = "questions"

urlpatterns = [
    path("<int:pk>/", views.QuestionDetailView.as_view(), name="detail"),
    path("<int:pk>/submit/", views.QuestionSubmitView.as_view(), name="submit"),
]

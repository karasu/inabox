from django.urls import path

from . import views

app_name = "app"

urlpatterns = [
    # /app
    path("", views.ChallengesIndexView.as_view(), name="challenges"),
    # /app/5
    path("<int:pk>/", views.ChallengeDetailView.as_view(), name="challenge_detail"),
]

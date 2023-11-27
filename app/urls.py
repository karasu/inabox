from django.urls import path

from . import views

app_name = "app"

urlpatterns = [
    # /app
    path("", views.PollsIndexView.as_view(), name="index"),
    path("challenges/", views.ChallengesIndexView.as_view(), name="challenges"),
    # /app/5
    path("challenges/<int:pk>/", views.ChallengeDetailView.as_view(), name="challenge_detail"),
]

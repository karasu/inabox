from django.urls import path

from . import views

app_name = "challenges"

urlpatterns = [
    # /challenges
    path("", views.ChallengesListView.as_view(), name="challenges"),
    # /challenges/5
    path("<int:pk>/", views.ChallengeDetailView.as_view(), name="challenge_detail"),
]

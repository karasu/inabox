from django.urls import path

from . import views

app_name = "challenges"

urlpatterns = [
    # /challenges
    path("", views.ChallengesListView.as_view(), name="challenges"),
    # /challenges/new
    path("new/", views.NewChallengeView.as_view(), name="new_challenge"),
    # /challenges/5
    path("<int:pk>/", views.ChallengeDetailView.as_view(), name="challenge_detail"),
]

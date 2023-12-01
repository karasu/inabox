from django.urls import path

from . import views

app_name = "Challenges"

urlpatterns = [
    # /challenges
    path("", views.ChallengesIndexView.as_view(), name="challenges"),
    # /challenge/5
    path("<int:pk>/", views.ChallengeDetailView.as_view(), name="challenge_detail"),
]

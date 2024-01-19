""" URLs module """

from django.urls import path

from . import views

app_name = "challenges"

urlpatterns = [
    # /challenges
    path("", views.ChallengesListView.as_view(),
        name="challenges"),
    # /challenges/5
    path("<int:pk>/", views.ChallengeDetailView.as_view(),
        name="challenge"),
    # /challenges/new
    path("new/", views.NewChallengeView.as_view(),
        name="new_challenge"),

    # /challenges/quests
    path("quests/", views.QuestsListView.as_view(),
        name="quests"),
    # /challenges/quests/5
    path("quests/<int:pk>/", views.QuestDetailView.as_view(),
        name="quest"),

    # /challenges/players
    path("players/", views.PlayersListView.as_view(),
        name="players"),
    # /challenges/players/5
    path("players/<int:pk>/", views.PlayerDetailView.as_view(),
        name="player"),

    # /challenges/teams
    path("teams/", views.TeamsListView.as_view(),
        name="teams"),
    # /challenges/teams/5
    path("teams/<int:pk>/", views.TeamDetailView.as_view(),
        name="team"),

    # /challenges/organizations
    path("organizations/", views.OrganizationsListView.as_view(),
        name="organizations"),
    # /challenges/organizations/5
    path("organizations/<int:pk>/", views.OrganizationDetailView.as_view(),
        name="organization"),

    path("search", views.SearchView.as_view(),
        name="search"),
    path("profile", views.ProfileView.as_view(),
        name="profile"),
]

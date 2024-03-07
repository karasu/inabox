""" URLs module """

from django.urls import path

from . import views

app_name = "app"

urlpatterns = [
    path("", views.NewsIndexView.as_view(), name="news"),
    path("about/", views.AboutView.as_view(), name="about"),

    path("signup/", views.SignUpView.as_view(), name="signup"),

    # /challenges
    path("challenges/", views.ChallengesListView.as_view(),
        name="challenges"),
    # /challenges/5
    path("challenges/<int:pk>/", views.ChallengeDetailView.as_view(),
        name="challenge"),
    # /challenges/new
    path("challenges/new/", views.NewChallengeView.as_view(),
        name="new_challenge"),

    # /quests
    path("quests/", views.QuestsListView.as_view(),
        name="quests"),
    # /quests/5
    path("quests/<int:pk>/", views.QuestDetailView.as_view(),
        name="quest"),

    # /players
    path("players/", views.PlayersListView.as_view(),
        name="players"),
    # /players/5
    path("players/<int:pk>/", views.PlayerDetailView.as_view(),
        name="player"),

    # /teams
    path("teams/", views.TeamsListView.as_view(),
        name="teams"),
    # /teams/5
    path("teams/<int:pk>/", views.TeamDetailView.as_view(),
        name="team"),

    # /organizations
    path("organizations/", views.OrganizationsListView.as_view(),
        name="organizations"),
    # /organizations/5
    path("organizations/<int:pk>/", views.OrganizationDetailView.as_view(),
        name="organization"),

    path("search/", views.SearchView.as_view(),
        name="search"),
    path("profile/<int:pk>", views.ProfileView.as_view(),
        name="profile"),

    # verify email urls
    path('verify-email/', views.VerifyEmailView.as_view(),
        name='verify-email'),
    path('verify-email-sent/', views.VerifyEmailSentView.as_view(),
        name='verify-email-sent'),
    path('verify-email-confirm/<uidb64>/<token>/', views.VerifyEmailConfirmView.as_view(),
        name='verify-email-confirm'),
    path('verify-email/complete/', views.VerifyEmailCompleteView.as_view(),
        name='verify-email-complete'),
]

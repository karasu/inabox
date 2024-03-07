""" URLs module """

from django.urls import path

from .views.about_view import AboutView
from .views.challenges_view import ChallengesListView, ChallengeDetailView
from .views.new_challenge_view import NewChallengeView
from .views.news_view import NewsView
from .views.organizations_view import OrganizationsListView, OrganizationDetailView
from .views.players_view import PlayersListView, PlayerDetailView
from .views.profile_view import ProfileView
from .views.quests_view import QuestsListView, QuestDetailView
from .views.search_view import SearchView
from .views.signup_view import SignUpView
from .views.teams_view import TeamsListView, TeamDetailView
from .views.verify_email_view import VerifyEmailView, VerifyEmailCompleteView
from .views.verify_email_view import VerifyEmailConfirmView, VerifyEmailSentView

app_name = "app"

urlpatterns = [
    path("", NewsView.as_view(), name="news"),
    path("about/", AboutView.as_view(), name="about"),

    path("signup/", SignUpView.as_view(), name="signup"),

    # /challenges
    path("challenges/", ChallengesListView.as_view(),
        name="challenges"),
    # /challenges/5
    path("challenges/<int:pk>/", ChallengeDetailView.as_view(),
        name="challenge"),
    # /challenges/new
    path("challenges/new/", NewChallengeView.as_view(),
        name="new_challenge"),

    # /quests
    path("quests/", QuestsListView.as_view(),
        name="quests"),
    # /quests/5
    path("quests/<int:pk>/", QuestDetailView.as_view(),
        name="quest"),

    # /players
    path("players/", PlayersListView.as_view(),
        name="players"),
    # /players/5
    path("players/<int:pk>/", PlayerDetailView.as_view(),
        name="player"),

    # /teams
    path("teams/", TeamsListView.as_view(),
        name="teams"),
    # /teams/5
    path("teams/<int:pk>/", TeamDetailView.as_view(),
        name="team"),

    # /organizations
    path("organizations/", OrganizationsListView.as_view(),
        name="organizations"),
    # /organizations/5
    path("organizations/<int:pk>/", OrganizationDetailView.as_view(),
        name="organization"),

    path("search/", SearchView.as_view(),
        name="search"),
    path("profile/<int:pk>", ProfileView.as_view(),
        name="profile"),

    # verify email urls
    path('verify-email/', VerifyEmailView.as_view(),
        name='verify-email'),
    path('verify-email-sent/', VerifyEmailSentView.as_view(),
        name='verify-email-sent'),
    path('verify-email-confirm/<uidb64>/<token>/', VerifyEmailConfirmView.as_view(),
        name='verify-email-confirm'),
    path('verify-email/complete/', VerifyEmailCompleteView.as_view(),
        name='verify-email-complete'),
]

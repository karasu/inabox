from django.urls import path

from . import views

urlpatterns = [
    # /challenges
    path("", views.index, name="index"),
    # /challenges/5
    path("<int:challenge_id>/", views.challenge, name="challenge"),
]

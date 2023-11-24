from django.urls import path

from . import views

app_name = "challenges"

urlpatterns = [
    # /challenges
    path("", views.IndexView.as_view(), name="index"),
    # /challenges/5
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
]

from django.urls import path

from . import views

app_name = "news"

urlpatterns = [
    # /news
    path("", views.NewsIndexView.as_view(), name="news"),
    path("about", views.AboutView.as_view(), name="about"),
]

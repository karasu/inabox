from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic

from .models import Challenge


class IndexView(generic.ListView):
    template_name = "challenges/index.html"
    context_object_name = "latest_challenge_list"

    def get_queryset(self):
        """ Return the last five published challenges. """
        return Challenge.objects.order_by("-pub_date")[:10]


class DetailView(generic.DetailView):
    model = Challenge

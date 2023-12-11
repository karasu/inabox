from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic

from .models import Challenge


class ChallengesListView(generic.ListView):
    template_name = "challenges/challenges.html"
    model = Challenge
    paginate_by = 10
    query_set = Challenge.objects.order_by("-pub_date")
  

class ChallengeDetailView(generic.DetailView):
    model = Challenge

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic

from .models import Challenge

'''
def index(request):
    latest_challenge_list = Challenge.objects.order_by("-pub_date")[:10]
    context = {"latest_challenge_list": latest_challenge_list}
    return render(request, "challenges/index.html", context)

def challenge(request, challenge_id):
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    return render(request, "challenges/challenge.html",
                   {"challenge": challenge})
'''

class IndexView(generic.ListView):
    template_name = "challenge/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """Return the last five published questions."""
        return Challenge.objects.order_by("-pub_date")[:5]


class DetailView(generic.DetailView):
    model = Challenge
    template_name = "polls/detail.html"
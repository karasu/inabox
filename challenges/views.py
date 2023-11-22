from django.shortcuts import get_object_or_404, render

# Create your views here.

from django.http import HttpResponse
from django.shortcuts import render

from .models import Challenge

def index(request):
    latest_challenge_list = Challenge.objects.order_by("-pub_date")[:10]
    context = {"latest_challenge_list": latest_challenge_list}
    return render(request, "challenges/index.html", context)

def challenge(request, challenge_id):
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    return render(request, "challenges/challenge.html",
                   {"challenge": challenge})

from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse
from django.shortcuts import render

from .models import Challenge

def index(request):
    latest_challenge_list = Challenge.objects.order_by("-pub_date")[:10]
    context = {"latest_challenge_list": latest_challenge_list}
    return render(request, "challenges/index.html", context)

def challenge(request, challenge_id):
    response = "You're looking at challenge %s."
    return HttpResponse(response % challenge_id)


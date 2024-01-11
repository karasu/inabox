from django.views import generic
from django.utils.translation import get_language
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
#from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseForbidden,  HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _


from .models import NewsEntry
from challenges.models import Profile

import logging

class NewsIndexView(generic.ListView):
    template_name = "news/news.html"
    model = NewsEntry
    paginate_by = 10

    def get_user_language(self):
        if self.request.user.is_authenticated:
            user_id = self.request.user.id
            profile = Profile.objects.get(user=user_id)
            return profile.language
        else:
            return get_language()

    #def get_queryset(self):
    #    """ Return the last five published news in the user's language """        
    #    return NewsEntry.objects.filter(language=self.get_user_language()).order_by("-pub_date")[:5]

class AboutView(generic.base.TemplateView):
    template_name = "news/about.html"




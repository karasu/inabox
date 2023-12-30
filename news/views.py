from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
#from django.contrib.auth import logout
from django.utils.timezone import now
from django.utils.translation import get_language

from .models import NewsEntry
from challenges.models import Profile


class NewsIndexView(generic.ListView):
    template_name = "news/news.html"
    model = NewsEntry
    paginate_by = 100

    def get_user_language(self):
        if self.request.user.is_authenticated:
            user_id = self.request.user.id
            profile = Profile.objects.get(user=user_id)
            return profile.language
        else:
            return get_language()

    def get_queryset(self):
        """ Return the last five published news """
        # NewsEntry.objects.
        
        return NewsEntry.objects.filter(language=self.get_user_language()).order_by("-pub_date")[:5]

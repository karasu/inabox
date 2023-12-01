from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic

from .models import NewsEntry


class NewsIndexView(generic.ListView):
    template_name = "news/news.html"
    context_object_name = "latest_news_list"

    def get_queryset(self):
        """ Return the last five published news. """
        return NewsEntry.objects.order_by("-pub_date")[:5]

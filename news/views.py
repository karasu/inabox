from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse


class NewsIndexView(generic.ListView):
    template_name = "news/news.html"
    context_object_name = "latest_news_list"

    def get_queryset(self):
        """ Return the last five published news. """
        return NewsEntry.objects.order_by("-pub_date")[:5]

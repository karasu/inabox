from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
#from django.contrib.auth import logout

from .models import NewsEntry


class NewsIndexView(generic.ListView):
    template_name = "news/news.html"
    model = NewsEntry
    paginate_by = 100

    def get_queryset(self):
        """ Return the last five published news. """
        return NewsEntry.objects.order_by("-pub_date")

'''
class LogoutView(generic.base.TemplateView):
    template_name = "logout.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        logout()
        return context
'''
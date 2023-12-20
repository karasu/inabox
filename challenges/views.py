from django.http import HttpResponseRedirect, JsonResponse, HttpResponseForbidden,  HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils.translation import gettext_lazy as _


from .models import Challenge
from .forms import ConnectSshForm


try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

class ChallengesListView(generic.ListView):
    template_name = "challenges/challenges.html"
    model = Challenge
    paginate_by = 10
    query_set = Challenge.objects.order_by("-pub_date")

# IndexHandler
class ChallengeDetailView(generic.DetailView):
    model = Challenge

    def get_context_data(self, **kwargs):
        # Add form to our context so we can put it in the template
        context = super(ChallengeDetailView, self).get_context_data(**kwargs)
        context['connect_ssh_form'] = ConnectSshForm
        return context

         

    def post(self, request, *args, **kwargs):

        # create a form instance and populate it with data from the request:
        form = ConnectSshForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            self.object = self.get_object()
            context = super(ChallengeDetailView, self).get_context_data(**kwargs)
            context['connect_ssh_form'] = form
            #return self.render_to_response(context=context)

            #print(context['challenge'].creator)
 
            

            self.result = dict(id=None, status=None, encoding=None)



            self.result.update(id=1, encoding='utf-8')

            return JsonResponse(self.result)
        else:
            #self.object = self.get_object()
            #context = super(ChallengeDetailView, self).get_context_data(**kwargs)
            #return self.render_to_response(context=context)
            return HttpResponseBadRequest()

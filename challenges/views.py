from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils.translation import gettext_lazy as _

from .models import Challenge

from .forms import ConnectSshForm


class ChallengesListView(generic.ListView):
    template_name = "challenges/challenges.html"
    model = Challenge
    paginate_by = 10
    query_set = Challenge.objects.order_by("-pub_date")
  

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

            print(context['challenge'].creator)
            self.result = dict(id=None, status=None, encoding=None)
 
            # TODO: codi client per cridar per websockets ssh
 
            self.result.update(status=_("SSH: Error trying to connect!"))
            return JsonResponse(self.result)
        else:
            print("FALSE")
            self.object = self.get_object()
            context = super(ChallengeDetailView, self).get_context_data(**kwargs)
            return self.render_to_response(context=context)



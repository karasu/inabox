from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic

from .models import Challenge

from .forms import ConnectForm


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
        context['connect_form'] = ConnectForm
        return context

    def is_ajax(self, request):
        return request.headers.get('x-requested-with') == 'XMLHttpRequest'

    def post(self, request, *args, **kwargs):

        # create a form instance and populate it with data from the request:
        form = ConnectForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            self.object = self.get_object()
            context = super(ChallengeDetailView, self).get_context_data(**kwargs)
            context['connect_form'] = form
            #return self.render_to_response(context=context)

            data = form.cleaned_data
            print(data)
            return JsonResponse(data) 

        else:
            print("FALSE")
            self.object = self.get_object()
            context = super(ChallengeDetailView, self).get_context_data(**kwargs)
            return self.render_to_response(context=context)



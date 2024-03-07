""" Search view """

from django.views import generic
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render

from ..forms import SearchForm
from ..models import Quest, Challenge


class SearchView(generic.base.TemplateView):
    """ search view """
    template_name = "app/search.html"

    def get(self, request, *args, **kwargs):
        form = SearchForm(request.GET)

        if form.is_valid():
            search_term = request.GET['search']
            # Try to find a challenge title or a quest title that has that term
            context = {}
            context['search_term'] = search_term

            # Search in quests title and creator
            context['quests'] = []
            quests = Quest.objects.filter(title__icontains=search_term) | \
                Quest.objects.filter(creator__username__icontains=search_term)
            for quest in quests:
                context['quests'].append(quest)

            num_quests = len(context['quests'])
            if  num_quests > 0:
                if num_quests > 1:
                    context['quests_found'] = _(f"{num_quests} quests found")
                else:
                    context['quests_found'] = _("One quest found")

            # Search in challenges title and creator
            context['challenges'] = []
            challenges = Challenge.objects.filter(title__icontains=search_term) | \
                Challenge.objects.filter(creator__username__icontains=search_term)
            for challenge in challenges:
                context['challenges'].append(challenge)

            num_challenges = len(context['challenges'])
            if  num_challenges > 0:
                if num_challenges > 1:
                    context['challenges_found'] = _(f"Found {num_challenges} challenges")
                else:
                    context['challenges_found'] = _("Found 1 challenge")

            return self.render_to_response(context=context)

        # Form is not valid
        return render(
            request,
            template_name=self.template_name,
            context={'form': form})

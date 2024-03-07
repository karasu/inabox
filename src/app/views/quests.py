""" Quests and quest views """

from django.views import generic
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.models import User

from ..models import Quest, QuestChallenge
from ..models import LEVELS

class QuestsListView(generic.ListView):
    """ List all quests """
    template_name = "app/quests.html"
    model = Quest
    paginate_by = 10

    def get_queryset(self):
        new_qs = Quest.objects.order_by("-pub_date")

        if self.request.GET:
            creator = self.request.GET.get('creator', 'all')
            level = self.request.GET.get('level', 'all')
            order = self.request.GET.get('order', 'newest')

            # Filter challenges list
            if creator != 'all':
                creator_id = User.objects.get(username=creator)
                new_qs = new_qs.filter(creator=creator_id)

            if level != 'all':
                new_qs = new_qs.filter(level=level)

            if order == 'newest':
                new_qs = new_qs.order_by("-pub_date")
            else:
                new_qs = new_qs.order_by("pub_date")

        return new_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['creators'] = User.objects.values_list('username', flat=True)
        context['levels'] = LEVELS

        context['screator'] = self.request.GET.get('creator', 'all')
        context['slevel'] = self.request.GET.get('level', 'all')
        context['sorder'] = self.request.GET.get('order', 'newest')

        return context


class QuestDetailView(generic.DetailView):
    """ Show quest information """
    model = Quest
    template_name = "app/quest.html"
    # challenge_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['challenge_list'] = []
        for quest_challenge in QuestChallenge.objects.filter(quest=context['quest']):
            context['challenge_list'].append(quest_challenge.challenge)
        return context


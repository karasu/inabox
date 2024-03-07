""" Teams and team views """

from django.views import generic
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

from ..models import Team

class TeamsListView(generic.ListView):
    """ List of teams """
    template_name = "app/teams.html"
    model = Team
    paginate_by = 10

class TeamDetailView(generic.DetailView):
    """ Team details """
    template_name = "app/team.html"
    model = Team

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["members"] = User.objects.filter(
            profile__team__id=context['team'].id)
        return context

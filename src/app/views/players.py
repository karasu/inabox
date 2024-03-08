""" Players and player views """

from django.views import generic
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User


class PlayersListView(generic.ListView):
    """ Show a list of all players (users) """
    template_name = "app/players.html"
    model = User
    paginate_by = 10


class PlayerDetailView(generic.DetailView):
    """ Show player's detail info (nothing personal) """
    model = User
    template_name = "app/player.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["player"] = context["user"]
        context['user'] = self.request.user
        return context

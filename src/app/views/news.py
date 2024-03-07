""" News view """

from django.views import generic
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language

from ..models import NewsEntry, Profile

class NewsView(generic.ListView):
    """ News view class """
    template_name = "app/news.html"
    model = NewsEntry
    paginate_by = 10

    def get_user_language(self):
        """ get user's chosen language """
        if self.request.user.is_authenticated:
            user_id = self.request.user.id
            profile = Profile.objects.get(user=user_id)
            return profile.language

        return get_language()

    #def get_queryset(self):
    #    """ Return the last five published news in the user's language """
    #    return NewsEntry.objects.filter(
    # language=self.get_user_language()).order_by("-pub_date")[:5]
    
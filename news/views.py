""" Put news app views here """

from django.views import generic
from django.utils.translation import get_language

from challenges.models import Profile
from .models import NewsEntry


class NewsIndexView(generic.ListView):
    """ News view class """
    template_name = "news/news.html"
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

class AboutView(generic.base.TemplateView):
    """ View to show about page """
    template_name = "news/about.html"

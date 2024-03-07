""" Organizations and organization view """

from django.views import generic
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

from ..models import Organization


class OrganizationsListView(generic.ListView):
    """ List of organizations """
    template_name = "app/organizations.html"
    model = Organization
    paginate_by = 10

class OrganizationDetailView(generic.DetailView):
    """ Organization details """
    template_name = "app/organization.html"
    model = Organization

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["members"] = User.objects.filter(
            profile__organization__id=context['organization'].id)
        return context

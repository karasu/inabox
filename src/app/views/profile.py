""" Profile view """

from django.views import generic
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from ..models import Profile
from ..forms import ProfileForm


class ProfileView(LoginRequiredMixin, generic.DetailView):
    """ Show user's profile """
    template_name = "app/profile.html"
    model = Profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['user'] = self.request.user
        context['form'] = ProfileForm(instance=context['profile'])

        return context

    def post(self, request, pk):
        """ Deal with post data here """
        if request.method == "POST":
           
            form = ProfileForm(request.POST, request.FILES)
            
            if form.is_valid():
                form.save()
                return redirect("profile", pk=pk)

            # Form is not valid
            return render(
                request,
                template_name=self.template_name,
                context={'user': request.user, 'form': form})

        raise PermissionDenied()

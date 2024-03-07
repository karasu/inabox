""" Profile view """

from django.views import generic
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from ..forms import ProfileForm


class ProfileView(LoginRequiredMixin, generic.base.TemplateView):
    """ Show user's profile """
    template_name = "app/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['form'] = ProfileForm(instance=self.request.user.profile)

        return context

    def post(self, request):
        """ Deal with post data here """
        user = self.request.user
        profile = user.profile

        if request.method == "POST":
            # Save user's profile data form
            form = ProfileForm(
                request.POST, request.FILES,
                instance=profile)
            if form.is_valid():
                form.save()
        else:
            # Show form with current user's profile data
            form = ProfileForm(
                instance=profile)

        return render(request, self.template_name, {
            'user': user,
            'profile': profile,
            'form': form }) 

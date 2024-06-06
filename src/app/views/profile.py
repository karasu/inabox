""" Profile view """

from django.views import generic
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from ..forms import ProfileForm, UserForm


class ProfileView(LoginRequiredMixin, generic.base.TemplateView):
    """ Show user's profile """
    template_name = "app/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user
        context['user_form'] = UserForm(instance=user)
        context['profile_form'] = ProfileForm(instance=user.profile)

        return context

    def post(self, request):
        """ Deal with post data here """
        user = self.request.user
        profile = user.profile

        if request.method == "POST":
            # Save user's data form
            user_form = UserForm(request.POST, instance=request.user)
            # Save user's profile data form
            profile_form = ProfileForm(
                request.POST, request.FILES,
                instance=profile)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()

        else:
            # Show form with current user's profile data
            user_form = UserForm(request.POST, instance=user)
            profile_form = ProfileForm(instance=profile)

        return render(request, self.template_name, {
            'user': user,
            'profile': profile,
            'user_form': user_form,
            'profile_form': profile_form }) 

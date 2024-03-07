""" New challenge view """

from django.shortcuts import render, redirect
from django.views import generic
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from ..forms import NewChallengeForm

class NewChallengeView(LoginRequiredMixin, generic.base.TemplateView):
    """ New challenge view """
    template_name="app/new_challenge.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["new_challenge_form"] = NewChallengeForm(user_id=self.request.user.id)
        return context

    def post(self, request):
        """ Deal with post data here """
        if request.method == "POST":
            form = NewChallengeForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                return redirect("challenges")

            # Form is not valid
            return render(
                request,
                template_name=self.template_name,
                context={'form': form})

        raise PermissionDenied()

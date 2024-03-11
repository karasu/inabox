""" Signup view """

from django.shortcuts import render, redirect
from django.views import generic
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import login

from ..forms import SignUpForm


# https://python.plainenglish.io/how-to-send-email-with-verification-link-in-django-efb21eefffe8
class SignUpView(generic.base.TemplateView):
    """ Allows a new user to register """
    template_name = "app/signup.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = SignUpForm()
        return context

    def post(self, request, *_args, **_kwargs):
        """ User wants to sign up """
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = form.save()
            # profile is saved in signals.py
            login(request, user,
                  backend='django.contrib.auth.backends.ModelBackend')
            return redirect('/verify-email/', request=request)

        # Form is not valid
        return render(
            request,
            template_name=self.template_name,
            context={'form': form})

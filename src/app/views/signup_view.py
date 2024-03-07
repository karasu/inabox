""" app views go here """

import socket
import os
import traceback
import asyncio

from concurrent.futures import ThreadPoolExecutor

from django.http import HttpResponseBadRequest
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import generic
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.utils.translation import get_language
# from django.utils.translation import get_language_info
from django.template.defaulttags import register
from django.core.exceptions import PermissionDenied

from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib import messages

import paramiko

from smtplib import SMTPAuthenticationError

from .args import Args
from .container import Image as DockerImage

from .forms import ChallengeSSHForm, CommentForm, NewChallengeForm
from .forms import UploadSolutionForm, SearchForm, StartAgainForm
from .forms import SignUpForm, ProfileForm

from .models import Challenge, Area, Profile, ProposedSolution, Quest, QuestChallenge
#from .models import ClassGroup
from .models import Team, Organization, Comment
#from .models import DockerImage
from .models import UserChallengeContainer, UserChallengeImage
from .models import LEVELS, ROLES
from .models import NewsEntry

from .privatekey import InvalidValueError
from .sshclient import SSHClient

from .tasks import validate_solution_task
from .tasks import run_container_task, commit_container_task
from .tasks import remove_container_task, remove_image_task

from .logger import g_logger

from .token import account_activation_token
from .utils import to_str

from .worker import Worker, recycle_worker, clients

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
            profile = Profile(user=user)
            profile.save()
            #login(request, user, backend='django_auth_ldap.backend.LDAPBackend')
            login(request, user,
                  backend='django.contrib.auth.backends.ModelBackend')
            return redirect('/verify-email', request=request)

        # Form is not valid
        return render(
            request,
            template_name=self.template_name,
            context={'form': form})


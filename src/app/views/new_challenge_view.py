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


@register.filter
def get_item(dictionary, key):
    """ Filter to get dict item in a loop """
    return dictionary.get(key)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Maximum live connections (ssh sessions) per client
MAXCONN=20

# The delay to call recycle_worker
RECYLE_WORKER_DELAY=3

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


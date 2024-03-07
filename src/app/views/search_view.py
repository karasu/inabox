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

class SearchView(generic.base.TemplateView):
    """ search view """
    template_name = "app/search.html"

    def get(self, request, *args, **kwargs):
        form = SearchForm(request.GET)

        if form.is_valid():
            search_term = request.GET['search']
            # Try to find a challenge title or a quest title that has that term
            context = {}
            context['search_term'] = search_term

            # Search in quests title and creator
            context['quests'] = []
            quests = Quest.objects.filter(title__icontains=search_term) | \
                Quest.objects.filter(creator__username__icontains=search_term)
            for quest in quests:
                context['quests'].append(quest)

            num_quests = len(context['quests'])
            if  num_quests > 0:
                if num_quests > 1:
                    context['quests_found'] = _(f"{num_quests} quests found")
                else:
                    context['quests_found'] = _("One quest found")

            # Search in challenges title and creator
            context['challenges'] = []
            challenges = Challenge.objects.filter(title__icontains=search_term) | \
                Challenge.objects.filter(creator__username__icontains=search_term)
            for challenge in challenges:
                context['challenges'].append(challenge)

            num_challenges = len(context['challenges'])
            if  num_challenges > 0:
                if num_challenges > 1:
                    context['challenges_found'] = _(f"Found {num_challenges} challenges")
                else:
                    context['challenges_found'] = _("Found 1 challenge")

            return self.render_to_response(context=context)

        # Form is not valid
        return render(
            request,
            template_name=self.template_name,
            context={'form': form})

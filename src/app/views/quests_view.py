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


class QuestsListView(generic.ListView):
    """ List all quests """
    template_name = "app/quests.html"
    model = Quest
    paginate_by = 10

    def get_queryset(self):
        new_qs = Quest.objects.order_by("-pub_date")

        if self.request.GET:
            creator = self.request.GET.get('creator', 'all')
            level = self.request.GET.get('level', 'all')
            order = self.request.GET.get('order', 'newest')

            # Filter challenges list
            if creator != 'all':
                creator_id = User.objects.get(username=creator)
                new_qs = new_qs.filter(creator=creator_id)

            if level != 'all':
                new_qs = new_qs.filter(level=level)

            if order == 'newest':
                new_qs = new_qs.order_by("-pub_date")
            else:
                new_qs = new_qs.order_by("pub_date")

        return new_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['creators'] = User.objects.values_list('username', flat=True)
        context['levels'] = LEVELS

        context['screator'] = self.request.GET.get('creator', 'all')
        context['slevel'] = self.request.GET.get('level', 'all')
        context['sorder'] = self.request.GET.get('order', 'newest')

        return context


class QuestDetailView(generic.DetailView):
    """ Show quest information """
    model = Quest
    template_name = "app/quest.html"
    # challenge_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['challenge_list'] = []
        for quest_challenge in QuestChallenge.objects.filter(quest=context['quest']):
            context['challenge_list'].append(quest_challenge.challenge)
        return context


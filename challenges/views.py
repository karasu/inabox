""" Challenges app views go here """

import socket
import os
import logging
import traceback
import asyncio

from concurrent.futures import ThreadPoolExecutor

from django.http import HttpResponseRedirect, HttpResponseForbidden,  HttpResponseBadRequest
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import generic
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.utils.translation import get_language, get_language_info
from django.template.defaulttags import register

import paramiko

from .sshclient import SSHClient
from .args import Args
from .privatekey import InvalidValueError

from .worker import Worker, recycle_worker, clients

from .models import Challenge, Area, Profile, ProposedSolution, Quest, QuestChallenge
from .models import ClassGroup, Team, Organization
from .models import LEVELS, ROLES
from .forms import ChallengeSSHForm, NewChallengeForm, UploadSolutionForm, SearchForm

# Celery task to check if a proposed solution is valid or not
from .tasks import validate_solution_task

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
    template_name="challenges/new_challenge.html"

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
                return HttpResponseRedirect(reverse("challenges:challenges"))
            else:
                logging.error(form.errors)
                return render(
                    request,
                    template_name="challenges/form_error.html",
                    context={
                        "title": _("Error inserting a new Challenge! Check the error(s) below:"),
                        "errors": form.errors,
                    })
        else:
            return HttpResponseForbidden()


class QuestsListView(generic.ListView):
    """ List all quests """
    template_name = "challenges/quests.html"
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
    template_name = "challenges/quest.html"
    # challenge_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['challenge_list'] = []
        for quest_challenge in QuestChallenge.objects.filter(quest=context['quest']):
            context['challenge_list'].append(quest_challenge.challenge)
        return context


class ChallengesListView(generic.ListView):
    """ Lists all challenges """
    template_name = "challenges/challenges.html"
    model = Challenge
    paginate_by = 10
    #query_set = Challenge.objects.order_by("-pub_date")

    def get_user_language(self):
        """ Returns user preferred language """
        if self.request.user.is_authenticated:
            user_id = self.request.user.id
            profile = Profile.objects.get(user=user_id)
            return profile.language
        return get_language()

    def get_queryset(self):
        # new_qs = Challenge.objects.all()
        new_qs = Challenge.objects.order_by("-pub_date")

        if self.request.GET:
            area = self.request.GET.get('area', 'all')
            creator = self.request.GET.get('creator', 'all')
            lang = self.request.GET.get('lang', 'all')
            level = self.request.GET.get('level', 'all')
            order = self.request.GET.get('order', 'newest')

            # Filter challenges list

            if area != 'all':
                area_id = Area.objects.get(name=area)
                new_qs = new_qs.filter(area=area_id)

            if creator != 'all':
                creator_id = User.objects.get(username=creator)
                new_qs = new_qs.filter(creator=creator_id)

            if lang != 'all':
                new_qs = new_qs.filter(language=lang)

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
        context['areas'] = Area.objects.values_list('name', flat=True)
        context['levels'] = LEVELS

        context['sarea'] = self.request.GET.get('area', 'all')
        context['screator'] = self.request.GET.get('creator', 'all')
        context['slang'] = self.request.GET.get('lang', 'all')
        context['slevel'] = self.request.GET.get('level', 'all')
        context['sorder'] = self.request.GET.get('order', 'newest')

        return context


class ChallengeDetailView(generic.DetailView):
    """ Show challenge class view """
    model = Challenge
    template_name = "challenges/challenge.html"
    executor = ThreadPoolExecutor(max_workers=os.cpu_count()*5)
    loop = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            # Add forms to our context so we can put them in the template
            di = context['challenge'].docker_image
            data = {
                "hostname": "localhost",
                "port": di.container_ssh_port,
                "username": di.container_username,
                "password": di.container_password,
                "privatekey": di.container_privatekey,
                "passphrase": di.container_passphrase,
                "totp": 0,
                "term": "xterm-256color",
                "challenge_id": context['challenge'].id,
            }
            context['ssh_data'] = ChallengeSSHForm(data)

            context['upload_solution_form'] = UploadSolutionForm(
                user_id = self.request.user.id,
                challenge_id = context['challenge'].id
            )

            try:
                context['proposed'] = ProposedSolution.objects.get(
                    user=self.request.user,
                    challenge=context['challenge'])
            except ProposedSolution.DoesNotExist:
                # it does not exist, create it
                context['proposed'] = ProposedSolution.objects.create(
                    user=self.request.user,
                    challenge=context['challenge'],
                    tries=0)
            except ProposedSolution.MultipleObjectsReturned:
                logging.error("Multiple entries in ProposedSolution table!")

        return context

    def load_host_keys(self, path):
        """ Get host keys """
        if os.path.exists(path) and os.path.isfile(path):
            return paramiko.hostkeys.HostKeys(filename=path)
        return paramiko.hostkeys.HostKeys()

    def get_host_keys_settings(self):
        """ Get host keys configuration """
        host_keys_filename = os.path.join(base_dir, 'known_hosts')
        host_keys = self.load_host_keys(host_keys_filename)

        filename = os.path.expanduser('~/.ssh/known_hosts')
        system_host_keys = self.load_host_keys(filename)

        settings = {
            "host_keys": host_keys,
            "system_host_keys": system_host_keys,
            "host_keys_filename": host_keys_filename
        }
        return settings

    def get_ssh_client(self):
        """ Create an ssh client """
        ssh = SSHClient()
        self.host_keys_settings = self.get_host_keys_settings()
        ssh._system_host_keys = self.host_keys_settings['system_host_keys']
        ssh._host_keys = self.host_keys_settings['host_keys']
        ssh._host_keys_filename = self.host_keys_settings['host_keys_filename']
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #ssh.set_missing_host_key_policy(self.policy)
        return ssh

    def ssh_connect(self, args):
        """ Connect to the container """
        ssh = self.ssh_client
        dst_addr = args[:2]
        logging.info('Connecting to {}:{}'.format(*dst_addr))

        try:
            #ssh.connect(*args, timeout=options.timeout)
            ssh.connect(*args, timeout=1)
        except socket.error:
            raise ValueError(_('Unable to connect to {}:{}').format(*dst_addr))
        except paramiko.BadAuthenticationType:
            raise ValueError(_('Bad authentication type.'))
        except paramiko.AuthenticationException:
            raise ValueError(_('Authentication failed.'))
        except paramiko.BadHostKeyException:
            raise ValueError(_('Bad host key.'))

        # term = self.get_argument('term', u'') or u'xterm'
        term = 'xterm'
        chan = ssh.invoke_shell(term=term)
        chan.setblocking(0)

        if self.loop is None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.loop = asyncio.get_event_loop()

        worker = Worker(self.loop, ssh, chan, dst_addr)
        #worker.encoding = options.encoding if options.encoding else \
        #    self.get_default_encoding(ssh)
        worker.encoding = "utf-8"
        return worker

    def get_client_ip_and_port(self, request):
        """ Reads info from header """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # running behind a proxy
            ip = x_forwarded_for.split(',')[0]
            port = request.META.get('HTTP_X_FORWARDED_PORT')
        else:
            ip = request.META.get('REMOTE_ADDR')
            port = request.META.get('REMOTE_PORT')
        return (ip, port)

    def challenge_ssh_form(self, request):
        """ Create a form instance and populate it with data from the request: """
        form = ChallengeSSHForm(request.POST)

        if form.is_valid():
            # Prepare SSH connection

            #self.policy = policy
            #self.host_keys_settings = host_keys_settings
            self.ssh_client = self.get_ssh_client()
            #self.debug = self.settings.get('debug', False)
            #self.font = self.settings.get('font', '')
            self.result = {
                'workerid': None,
                'status': None,
                'encoding':None
            }

            src_ip, src_port = self.get_client_ip_and_port(request)
            #print(ip, port)
            workers = clients.get(src_ip, {})
            if workers and len(workers) >= MAXCONN:
                return HttpResponseForbidden(_('Too many live connections.'))

            # TODO: check origin
            #self.check_origin()

            try:
                _args = Args(request).get_args()
            except InvalidValueError as exc:
                return HttpResponseBadRequest(str(exc))

            future = self.executor.submit(self.ssh_connect, _args)

            try:
                 #worker = yield future
                worker = future.result()
            except (ValueError, paramiko.SSHException) as exc:
                logging.error(traceback.format_exc())
                self.result.update(status=str(exc))
            else:
                if not workers:
                    clients[src_ip] = workers
                worker.src_addr = (src_ip, src_port)
                workers[worker.id] = worker
                self.loop.call_later(
                    RECYLE_WORKER_DELAY, recycle_worker, worker)

                self.result.update(
                    workerid=worker.id, status='', encoding=worker.encoding)

            return JsonResponse(self.result)

        # form is not valid
        logging.error(form.errors)
        return render(
            request,
            template_name="challenges/form_error.html",
            context={
                "title": _("Error form data trying to connect! Check the error(s) below:"),
                "errors": form.errors,
                }
            )

    def upload_solution_form(self, request):
        """ We need to check if user has already tried and update the ProposedSolution
        if not just save this as the first one """
        user = request.POST.get('user')
        challenge = request.POST.get('challenge')
        proposed_solution = ProposedSolution.objects.get(
            user=user,
            challenge=challenge)

        if proposed_solution:
            # Update user's tries
            proposed_solution.tries = proposed_solution.tries + 1
            proposed_solution.save()

        form = UploadSolutionForm(
            request.POST,
            request.FILES,
            instance=proposed_solution)

        if form.is_valid():
            form.save()
            # Update tries field for this challenge
            # I know, this is redundant, but it's easier this way
            challenge = Challenge.objects.get(id=challenge)
            challenge.total_tries = challenge.total_tries + 1
            challenge.save()

            # Tell Celery to test the uploaded solution so we don't
            # have to wait for it
            proposed_solution = ProposedSolution.objects.get(
                user=user,
                challenge=challenge)

            res = validate_solution_task.delay(proposed_solution.id)
            # Get task id
            #task_id = validate_solution_task.task_id
            task_id = res.id
            print(res.id, res.status)
            #context = super().get_context_data(**kwargs)
            context = self.get_context_data(**kwargs)
            context['task_id'] = task_id

            return self.render_to_response(context=context)

        # Form is not valid
        logging.error(form.errors)
        return render(
            request,
            template_name="challenges/form_error.html",
            context={
                "title": _("Error uploading a new solution! Check the error(s) below:"),
                "errors": form.errors,
                }
            )

    def post(self, request, *args, **kwargs):
        """ Deal with post data """
        # assign the object to the view
        self.object = self.get_object()

        # check that user is authenticated
        if not request.user.is_authenticated:
            return HttpResponseForbidden()

        if request.POST.get("form_name") == "UploadSolutionForm":
            return self.upload_solution_form(request)

        if request.POST.get("form_name") == "ChallengeSSHForm":
            return self.challenge_ssh_form(request)

        return HttpResponseBadRequest()

class SearchView(generic.base.TemplateView):
    """ search view """
    template_name = "challenges/search.html"

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
                    context['quests_found'] = _("{} quests found").format(num_quests)
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
                    context['challenges_found'] = _("Found {} challenges").format(num_challenges)
                else:
                    context['challenges_found'] = _("Found 1 challenge")

            return self.render_to_response(context=context)
        else:
            logging.error(form.errors)
            return render(
                request,
                template_name="challenges/form_error.html",
                context={
                    "title": _("Error in search form. Check the error(s) below:"),
                    "errors": form.errors,
                })

class ProfileView(LoginRequiredMixin, generic.base.TemplateView):
    """ Show user's profile """
    template_name = "challenges/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = ROLES

        objs = {
            "user": User.objects.get(id=self.request.user.id),
            "profile": Profile.objects.get(user=self.request.user)
        }

        excludes = {
            "user": [
                "id", "password", "groups", "user_permissions", "profile"],
            "profile": [
                "id", "user", "private_key", "challenge", "dockercontainer",
                "proposedsolution", "quest", "logentry"]}

        for k, obj in objs.items():
            context[k + "_data"] = []
            for field in obj._meta.get_fields():
                if field.name not in excludes[k]:
                    try:
                        label = field.verbose_name.capitalize()
                        value = field.value_from_object(obj)

                        if field.name == "teacher":
                            value = User.objects.get(id=value)

                        if field.name == "role":
                            for (myid, desc) in ROLES:
                                if myid == value:
                                    value = desc

                        if field.name == "class_group":
                            value = ClassGroup.objects.get(id=value)

                        if field.name == "language":
                            lang_info = get_language_info(value)
                            value = lang_info["name_translated"]

                        if field.name == "team":
                            value = Team.objects.get(id=value)

                        if field.name == "organization":
                            value = Organization.objects.get(id=value)

                        context[k + "_data"].append(
                            {"name": field.name,
                            "label": label,
                            "value": value})
                    except AttributeError as err:
                        print(err)

        return context


class PlayersListView(generic.ListView):
    """ Show a list of all players (users) """
    template_name = "challenges/players.html"
    model = User
    paginate_by = 10


class PlayerDetailView(generic.DetailView):
    """ Show player's detail info (nothing personal) """
    model = User
    template_name = "challenges/player.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["player"] = context["user"]
        return context

class OrganizationsListView(generic.ListView):
    """ List of organizations """
    template_name = "challenges/organizations.html"
    model = Organization
    paginate_by = 10

class OrganizationDetailView(generic.DetailView):
    """ Organization details """
    template_name = "challenges/organization.html"
    model = Organization

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["members"] = User.objects.filter(
            profile__organization__id=context['organization'].id)
        return context

class TeamsListView(generic.ListView):
    """ List of teams """
    template_name = "challenges/teams.html"
    model = Team
    paginate_by = 10

class TeamDetailView(generic.DetailView):
    """ Team details """
    template_name = "challenges/team.html"
    model = Team

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["members"] = User.objects.filter(
            profile__team__id=context['team'].id)
        return context

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseForbidden,  HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib.auth.models import User
from django.utils.translation import get_language

import paramiko
import socket

import os
import json
import logging
import struct
import traceback
import asyncio

from .sshclient import SSHClient
from .args import InvalidValueError, Args

try:
    from types import UnicodeType
except ImportError:
    UnicodeType = str

from concurrent.futures import ThreadPoolExecutor

from .utils import (
    is_valid_ip_address, is_valid_port, is_valid_hostname, to_bytes, to_str,
    to_int, to_ip_address, UnicodeType, is_ip_hostname, is_same_primary_domain,
    is_valid_encoding
)

from .worker import Worker, recycle_worker, clients

from .models import Challenge, Area, Profile, ProposedSolution, Quest, QuestChallenge
from .models import LEVELS
from .forms import ChallengeSSHForm, NewChallengeForm, UploadSolutionForm

# Celery task to check if a proposed solution is valid or not
from .tasks import validate_solution_task

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Maximum live connections (ssh sessions) per client
MAXCONN=20

# The delay to call recycle_worker
RECYLE_WORKER_DELAY=3

class NewChallengeView(LoginRequiredMixin, generic.base.TemplateView):
    template_name="challenges/new_challenge.html"
 
    def get_context_data(self, **kwargs):
        context = super(NewChallengeView, self).get_context_data(**kwargs)
        context["new_challenge_form"] = NewChallengeForm(user_id=self.request.user.id)
        return context
    
    def post(self, request, *args, **kwargs):
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
        context = super(QuestsListView, self).get_context_data(**kwargs)
        
        context['creators'] = User.objects.values_list('username', flat=True)
        context['levels'] = LEVELS

        context['screator'] = self.request.GET.get('creator', 'all')
        context['slevel'] = self.request.GET.get('level', 'all')
        context['sorder'] = self.request.GET.get('order', 'newest')

        return context


class QuestDetailView(generic.DetailView):
    model = Quest
    template_name = "challenges/quest.html"
    # challenge_list

    def get_context_data(self, **kwargs):
        context = super(QuestDetailView, self).get_context_data(**kwargs)
        context['challenge_list'] = []
        for quest_challenge in QuestChallenge.objects.filter(quest=context['quest']):
            context['challenge_list'].append(quest_challenge.challenge)
        return context


class ChallengesListView(generic.ListView):
    template_name = "challenges/challenges.html"
    model = Challenge
    paginate_by = 10
    #query_set = Challenge.objects.order_by("-pub_date")

    def get_user_language(self):
        if self.request.user.is_authenticated:
            user_id = self.request.user.id
            profile = Profile.objects.get(user=user_id)
            return profile.language
        else:
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
        context = super(ChallengesListView, self).get_context_data(**kwargs)
        
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
    model = Challenge
    template_name = "challenges/challenge.html"
    executor = ThreadPoolExecutor(max_workers=os.cpu_count()*5)
    loop = None

    def get_context_data(self, **kwargs):
        context = super(ChallengeDetailView, self).get_context_data(**kwargs)

        if (self.request.user.is_authenticated):
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
            context['challenge_ssh_form'] = ChallengeSSHForm(data)

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
        if os.path.exists(path) and os.path.isfile(path):
            return paramiko.hostkeys.HostKeys(filename=path)
        return paramiko.hostkeys.HostKeys()

    def get_host_keys_settings(self):
        host_keys_filename = os.path.join(base_dir, 'known_hosts')
        host_keys = self.load_host_keys(host_keys_filename)

        filename = os.path.expanduser('~/.ssh/known_hosts')
        system_host_keys = self.load_host_keys(filename)

        settings = dict(
            host_keys=host_keys,
            system_host_keys=system_host_keys,
            host_keys_filename=host_keys_filename
        )
        return settings

    def get_ssh_client(self):
        ssh = SSHClient()
        self.host_keys_settings = self.get_host_keys_settings()
        ssh._system_host_keys = self.host_keys_settings['system_host_keys']
        ssh._host_keys = self.host_keys_settings['host_keys']
        ssh._host_keys_filename = self.host_keys_settings['host_keys_filename']
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #ssh.set_missing_host_key_policy(self.policy)
        return ssh

    def ssh_connect(self, args):
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
        except paramiko.AuthenticationException as err:
            raise ValueError(_('Authentication failed.'))
        except paramiko.BadHostKeyException:
            raise ValueError(_('Bad host key.'))
        
        # term = self.get_argument('term', u'') or u'xterm'
        term = u'xterm'
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
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # running behind a proxy
            ip = x_forwarded_for.split(',')[0]
            port = request.META.get('HTTP_X_FORWARDED_PORT')
        else:
            ip = request.META.get('REMOTE_ADDR')
            port = request.META.get('REMOTE_PORT')
        return (ip, port)
    
    def challenge_ssh_form(self, request, *args, **kwargs):
        # create a form instance and populate it with data from the request:
        form = ChallengeSSHForm(request.POST)

        if form.is_valid():
            # Prepare SSH connection

            #self.policy = policy
            #self.host_keys_settings = host_keys_settings
            self.ssh_client = self.get_ssh_client()
            #self.debug = self.settings.get('debug', False)
            #self.font = self.settings.get('font', '')
            self.result = dict(workerid=None, status=None, encoding=None)

            src_ip, src_port = self.get_client_ip_and_port(request)
            #print(ip, port)
            workers = clients.get(src_ip, {})
            if workers and len(workers) >= MAXCONN:
                return HttpResponseForbidden(_('Too many live connections.'))

            #self.check_origin()
            try:
                form_args = Args(request)
                args = form_args.get_args()
            except InvalidValueError as exc:
                return HttpResponseBadRequest(str(exc))

            future = self.executor.submit(self.ssh_connect, args)

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
        else:
            logging.error(form.errors)
            return render(
                request,
                template_name="challenges/form_error.html",
                context={
                    "title": _("Error form data trying to connect! Check the error(s) below:"),
                    "errors": form.errors,
                    }
                )
    
    def upload_solution_form(self, request, *args, **kwargs):
        # We need to check if user has already tried and update the ProposedSolution
        # if not just save this as the first one
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
            #context = super(ChallengeDetailView, self).get_context_data(**kwargs)
            context = self.get_context_data(**kwargs)
            context['task_id'] = task_id
            
            return self.render_to_response(context=context)
            '''
            return render(
                request,
                template_name="challenges/challenge.html",
                context=context)
            '''
            #context = super(ChallengeDetailView, self).get_context_data(**kwargs)
            #return self.render_to_response(context=context)
        else:
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
        # assign the object to the view
        self.object = self.get_object()

        # check that user is authenticated
        if not request.user.is_authenticated:
            return HttpResponseForbidden()

        if request.POST.get("form_name") == "UploadSolutionForm":
            return self.upload_solution_form(request, *args, **kwargs)
  
        if request.POST.get("form_name") == "ChallengeSSHForm":
            return self.challenge_ssh_form(request, *args, **kwargs)

        return HttpResponseBadRequest()

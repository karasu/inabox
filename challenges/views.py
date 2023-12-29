from django.http import HttpResponseRedirect, JsonResponse, HttpResponseForbidden,  HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib.auth.models import User

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

from .models import Challenge, Area
from .forms import ChallengeSSHForm

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Maximum live connections (ssh sessions) per client
MAXCONN=20

# The delay to call recycle_worker
RECYLE_WORKER_DELAY=3


class ChallengesListView(generic.ListView):
    template_name = "challenges/challenges.html"
    model = Challenge
    paginate_by = 10
    #query_set = Challenge.objects.order_by("-pub_date")

    def get_queryset(self):
        # creator, order, area, difficulty
        new_qs = Challenge.objects.all()

        if self.request.GET:
            creator = self.request.GET.get('creator', 'all')
            order = self.request.GET.get('order', 'newest')
            area = self.request.GET.get('area', 'all')
            difficulty = self.request.GET.get('difficulty', 'all')
        
            if creator != 'all':
                creator_id = User.objects.get(username=creator)
                new_qs = new_qs.filter(creator=creator_id)
            if order == 'newest':
                new_qs = new_qs.order_by("-pub_date")
            else:
                new_qs = new_qs.order_by("pub_date")
            if area != 'all':
                area_id = Area.objects.get(name=area)
                new_qs = new_qs.filter(area=area_id)
        
        #new_qs = Challenge.objects.order_by("-pub_date")
        return new_qs

    def get_context_data(self, **kwargs):
        context = super(ChallengesListView, self).get_context_data(**kwargs)
        
        context['creators'] = User.objects.values_list('username', flat=True)
        context['areas'] = Area.objects.values_list('name', flat=True)
        context['levels'] = Challenge.LEVELS

        context['screator'] = self.request.GET.get('creator', 'all')
        context['sorder'] = self.request.GET.get('order', 'newest')
        context['sarea'] = self.request.GET.get('area', 'all')
        context['slevel'] = self.request.GET.get('level', 'newest')
        # print("get_context_data GET:", self.request.GET)
        #print(context)
        return context


# IndexHandler
class ChallengeDetailView(LoginRequiredMixin, generic.DetailView):
    model = Challenge
    executor = ThreadPoolExecutor(max_workers=os.cpu_count()*5)
    loop = None

    def get_context_data(self, **kwargs):
        # Add form to our context so we can put it in the template
        context = super(ChallengeDetailView, self).get_context_data(**kwargs)

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
        }
        context['challenge_ssh_form'] = ChallengeSSHForm(data)
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

        print("Connecting...")
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

        print("Creating worker...")
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
    
    def post(self, request, *args, **kwargs):
        # create a form instance and populate it with data from the request:
        form = ChallengeSSHForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            #print(request.META)
            #print("************")
            #print(request.POST)
            #print(context['challenge'].creator)

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

            print("POST result:", self.result)

            return JsonResponse(self.result)
        else:
            return HttpResponseForbidden()

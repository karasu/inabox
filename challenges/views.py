from django.http import HttpResponseRedirect, JsonResponse, HttpResponseForbidden,  HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils.translation import gettext_lazy as _

import paramiko
import socket

import os
import json
import logging
import os
import struct
import traceback

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

from .models import Challenge
from .forms import ConnectSshForm

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Maximum live connections (ssh sessions) per client
MAXCONN=20

class ChallengesListView(generic.ListView):
    template_name = "challenges/challenges.html"
    model = Challenge
    paginate_by = 10
    query_set = Challenge.objects.order_by("-pub_date")

# IndexHandler
class ChallengeDetailView(generic.DetailView):
    model = Challenge
    executor = ThreadPoolExecutor(max_workers=os.cpu_count()*5)

    def get_context_data(self, **kwargs):
        # Add form to our context so we can put it in the template
        context = super(ChallengeDetailView, self).get_context_data(**kwargs)
        context['connect_ssh_form'] = ConnectSshForm
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
            raise ValueError('Unable to connect to {}:{}'.format(*dst_addr))
        except paramiko.BadAuthenticationType:
            raise ValueError('Bad authentication type.')
        except paramiko.AuthenticationException:
            raise ValueError('Authentication failed.')
        except paramiko.BadHostKeyException:
            raise ValueError('Bad host key.')

        term = self.get_argument('term', u'') or u'xterm'
        chan = ssh.invoke_shell(term=term)
        chan.setblocking(0)
        worker = Worker(self.loop, ssh, chan, dst_addr)
        worker.encoding = options.encoding if options.encoding else \
            self.get_default_encoding(ssh)
        return worker

    def get_client_ip(self, request):
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
        form = ConnectSshForm(request.POST)
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
            self.result = dict(id=None, status=None, encoding=None)

            ip, port = self.get_client_ip(request)
            #print(ip, port)
            workers = clients.get(ip, {})
            if workers and len(workers) >= MAXCONN:
                return HttpResponseForbidden(_('Too many live connections.'))

            #self.check_origin()
            try:
                form_args = Args(request.POST)
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
                    clients[ip] = workers
                worker.src_addr = (ip, port)
                workers[worker.id] = worker
                self.loop.call_later(options.delay, recycle_worker, worker)
                self.result.update(id=worker.id, encoding=worker.encoding)



            return JsonResponse(self.result)
        else:
            return HttpResponseForbidden()

    '''
    def post(self, request, *args, **kwargs):
        
        # create a form instance and populate it with data from the request:
        form = ConnectSshForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            self.object = self.get_object()
            context = super(ChallengeDetailView, self).get_context_data(**kwargs)
            context['connect_ssh_form'] = form
            #return self.render_to_response(context=context)

            print(request.META)
            #print(context['challenge'].creator)
 
            #self.policy = policy
            #self.host_keys_settings = host_keys_settings
            self.ssh_client = self.get_ssh_client()
            #self.debug = self.settings.get('debug', False)
            #self.font = self.settings.get('font', '')
            self.result = dict(id=None, status=None, encoding=None)

            ip, port = self.get_client_ip(request)
            workers = clients.get(ip, {})
            if workers and len(workers) >= options.maxconn:
                return HttpResponseForbidden(_('Too many live connections.'))

            #self.check_origin()
            try:
                args = self.get_args()
            except InvalidValueError as exc:
                return HttpResponseBadRequest(str(exc))

            future = self.executor.submit(self.ssh_connect, args)

            try:
                worker = yield future
            except (ValueError, paramiko.SSHException) as exc:
                logging.error(traceback.format_exc())
                self.result.update(status=str(exc))
            else:
                if not workers:
                    clients[ip] = workers
                worker.src_addr = (ip, port)
                workers[worker.id] = worker
                self.loop.call_later(options.delay, recycle_worker, worker)
                self.result.update(id=worker.id, encoding=worker.encoding)

            return JsonResponse(self.result)
        else:
            #self.object = self.get_object()
            #context = super(ChallengeDetailView, self).get_context_data(**kwargs)
            #return self.render_to_response(context=context)
            return HttpResponseBadRequest()
    '''
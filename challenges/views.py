from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils.translation import gettext_lazy as _

from concurrent.futures import ThreadPoolExecutor

from webssh.utils import (
    is_valid_ip_address, is_valid_port, is_valid_hostname, to_bytes, to_str,
    to_int, to_ip_address, UnicodeType, is_ip_hostname, is_same_primary_domain,
    is_valid_encoding
)

from .models import Challenge
from .forms import ConnectSshForm

from .sshclient import SSHClient
from .worker import Worker, recycle_worker, clients

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

class ChallengesListView(generic.ListView):
    template_name = "challenges/challenges.html"
    model = Challenge
    paginate_by = 10
    query_set = Challenge.objects.order_by("-pub_date")

# IndexHandler
class ChallengeDetailView(generic.DetailView):
    model = Challenge

    def get_context_data(self, **kwargs):
        # Add form to our context so we can put it in the template
        context = super(ChallengeDetailView, self).get_context_data(**kwargs)
        context['connect_ssh_form'] = ConnectSshForm
        return context

    def get_ssh_client(self):
        ssh = SSHClient()
        ssh._system_host_keys = self.host_keys_settings['system_host_keys']
        ssh._host_keys = self.host_keys_settings['host_keys']
        ssh._host_keys_filename = self.host_keys_settings['host_keys_filename']
        #ssh.set_missing_host_key_policy(self.policy)
        return ssh

    def get_host_keys_settings(self):
        # TODO: Check that this returns correct values
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

    def load_host_keys(self, path):
        if os.path.exists(path) and os.path.isfile(path):
            return paramiko.hostkeys.HostKeys(filename=path)
        return paramiko.hostkeys.HostKeys()

    def ssh_connect(self, args):
        ssh = self.ssh_client

        #dst_addr = args[:2]
        #logging.info('Connecting to {}:{}'.format(*dst_addr))


        try:
            ssh.connect(*args, timeout=1)
        except socket.error:
            raise ValueError('Unable to connect.')
        except paramiko.BadAuthenticationType:
            raise ValueError('Bad authentication type.')
        except paramiko.AuthenticationException:
            raise ValueError('Authentication failed.')
        except paramiko.BadHostKeyException:
            raise ValueError('Bad host key.')

        #term = self.get_argument('term', u'') or u'xterm'
        term = u'xterm'
        chan = ssh.invoke_shell(term=term)
        chan.setblocking(0)

        worker = Worker(self.loop, ssh, chan, dst_addr)
        worker.encoding = options.encoding if options.encoding else \
            self.get_default_encoding(ssh)
        return worker
        

    def post(self, request, *args, **kwargs):
        self.host_keys_settings  = self.get_host_keys_settings()
        self.result = dict(id=None, status=None, encoding=None)

        # create a form instance and populate it with data from the request:
        form = ConnectSshForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            self.object = self.get_object()
            context = super(ChallengeDetailView, self).get_context_data(**kwargs)
            context['connect_ssh_form'] = form
            #return self.render_to_response(context=context)

            print(context['challenge'].creator)
 
            # TODO: IndexHandler
 
            #self.result.update(status=_("SSH: Error trying to connect!"))
            self.result.update(id=1, encoding='utf-8')
            return JsonResponse(self.result)
        else:
            self.object = self.get_object()
            context = super(ChallengeDetailView, self).get_context_data(**kwargs)
            return self.render_to_response(context=context)

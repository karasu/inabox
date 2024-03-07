""" app views go here """


import socket
import os
import traceback
import asyncio

from concurrent.futures import ThreadPoolExecutor

from django.http import HttpResponseBadRequest
from django.http import JsonResponse
from django.shortcuts import render
from django.views import generic
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.utils.translation import get_language
# from django.utils.translation import get_language_info
from django.core.exceptions import PermissionDenied

import paramiko

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

# Maximum live connections (ssh sessions) per client
MAXCONN=20

# The delay to call recycle_worker
RECYLE_WORKER_DELAY=3

class ChallengesListView(generic.ListView):
    """ Lists all challenges """
    template_name = "app/challenges.html"
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
    template_name = "app/challenge.html"
    executor = ThreadPoolExecutor(max_workers=os.cpu_count()*5)
    loop = None
    quest = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.quest:
            context['quest'] = self.quest

        if self.request.user.is_authenticated:
            # Add forms to our context so we can put them in the template

            # Get the docker image of this challenge
            docker_image = context['challenge'].docker_image

            # Get docker image and container id from db (if exist)
            cinfo = self.get_container_info(context['challenge'])

            # Get data for the SSH connection form
            data = {
                "hostname": "localhost",
                "port": docker_image.container_ssh_port,
                "username": docker_image.container_username,
                "password": docker_image.container_password,
                "privatekey": docker_image.container_privatekey,
                "passphrase": docker_image.container_passphrase,
                "totp": 0,
                "term": "xterm-256color",
                "challenge_id": context['challenge'].id,
                'image_name': cinfo['image_name'],
                'container_id': cinfo['container_id'],
            }
            context['ssh_data'] = ChallengeSSHForm(data)

            # Get data for the start again form
            data = {
                "challenge_id": context['challenge'].id,
                'image_name': cinfo['image_name'],
                'container_id': cinfo['container_id'],
            }
            context['start_again_data'] = StartAgainForm(data)

            # Get data for the upload solution form
            context['upload_solution_form'] = UploadSolutionForm(
                user_id = self.request.user.id,
                challenge_id = context['challenge'].id)

            # Get proposed solution data
            try:
                context['proposed'] = ProposedSolution.objects.get(
                    user=self.request.user,
                    challenge=context['challenge'])
            except ProposedSolution.DoesNotExist:
                # entry does not exist, create it
                context['proposed'] = ProposedSolution.objects.create(
                    user=self.request.user,
                    challenge=context['challenge'],
                    tries=0)
            except ProposedSolution.MultipleObjectsReturned:
                g_logger.error("Multiple entries in ProposedSolution table!")

            # Get data for comment form
            context['comment_form'] = CommentForm(
                user_id = self.request.user.id,
                challenge_id = context['challenge'].id)

        # Get active challenge's comments (even when user is not logged in)
        context['comments'] = context['challenge'].comments.filter(active=True)

        return context

    def get(self, request, *args, **kwargs):
        """ Check get data """
        self.quest = request.GET.get("quest", 0)
        return super().get(request, args, kwargs)

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
        ssh = SSHClient(self.get_host_keys_settings())
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #ssh.set_missing_host_key_policy(self.policy)
        return ssh

    def ssh_connect(self, args):
        """ Connect to the container """
        ssh = self.ssh_client
        dst_addr = args[:2]
        g_logger.info("Connecting to %s:%d", dst_addr[0], dst_addr[1])

        try:
            #ssh.connect(*args, timeout=options.timeout)
            ssh.connect(*args, timeout=1)
        except socket.error as exc:
            raise ValueError(f"Unable to connect to {dst_addr[0]}:{dst_addr[1]}") from exc
        except paramiko.BadAuthenticationType as exc:
            raise ValueError(_('Bad authentication type.')) from exc
        except paramiko.AuthenticationException as exc:
            raise ValueError(_('Authentication failed.')) from exc
        except paramiko.BadHostKeyException as exc:
            raise ValueError(_('Bad host key.')) from exc

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
            ip_address = x_forwarded_for.split(',')[0]
            port = request.META.get('HTTP_X_FORWARDED_PORT')
        else:
            ip_address = request.META.get('REMOTE_ADDR')
            port = request.META.get('REMOTE_PORT')
        return (ip_address, port)

    def get_container_info(self, challenge):
        """ Gets the docker container info stored in db """
        user = self.request.user
        image_name = challenge.docker_image.docker_name

        # Check if user has a previous saved image for this challenge
        # in UserChallengeImage
        try:
            uci = UserChallengeImage.objects.get(
                user=user,
                challenge=challenge
            )
            user_image_name = uci.image_name
        except UserChallengeImage.DoesNotExist:
            g_logger.debug("No previous saved image found.")
            user_image_name = None

        if user_image_name and DockerImage(user_image_name).is_ok():
            image_name = user_image_name
            container_id = None
        else:
            # No previous image found. Let's try a previous container.
            # If there is none, a new container will be created later
            try:
                ucc = UserChallengeContainer.objects.get(
                    user=user,
                    challenge=challenge
                )
                container_id = ucc.container_id
            except UserChallengeContainer.DoesNotExist:
                g_logger.debug("No previous container found.")
                container_id = None
        return {'image_name': image_name, 'container_id': container_id }

    def start_again(self, request, *_args, **kwargs):
        """ User wants to discard all container changes and start anew """

        form_data = request.POST
        form = StartAgainForm(form_data)

        if form.is_valid():
            user = self.request.user
            challenge_id = form_data.get('challenge_id')
            challenge = Challenge.objects.get(id=challenge_id)
            image_name = form_data.get('image_name', None)
            container_id = form_data.get('container_id', None)

            # Delete saved docker image and container references from db
            try:
                uci = UserChallengeImage.objects.get(
                    user=user,
                    challenge=challenge)
                uci.delete()
                g_logger.debug("Docker image reference has been removed from db. That's ok.")
            except UserChallengeImage.DoesNotExist:
                g_logger.debug(
                    "Did not find any docker image reference to remove from db. That's ok.")

            try:
                ucc = UserChallengeContainer.objects.get(
                    user=user,
                    challenge=challenge)
                ucc.delete()
                g_logger.debug("Docker container reference has been removed from db. That's ok")
            except UserChallengeContainer.DoesNotExist:
                g_logger.debug(
                    "Did not find any docker container reference to remove in db. That's ok")

            # Delete container and image (if image is different from the base one)
            if container_id:
                # delete container
                remove_container_task.delay(container_id=container_id)

            if image_name and image_name != challenge.docker_image.docker_name:
                remove_image_task.delay(image_name=image_name)

            context = self.get_context_data(**kwargs)
            return self.render_to_response(context=context)

        return render(
            request,
            template_name=self.template_name,
            context={'form': form})

    def challenge_ssh_form(self, request):
        """ Create a form instance and populate it with data from the request: """

        form = ChallengeSSHForm(request.POST)

        if form.is_valid():
            challenge_id = request.POST.get('challenge_id')
            challenge = Challenge.objects.get(id=challenge_id)

            # Get docker image and container id (if exist)
            #image_name, container_id = self.prepare_container(challenge)
            image_name = request.POST.get('image_name', None)
            container_id = request.POST.get('container_id', None)

            user = self.request.user
            # Run the container
            # (the one that exists or a new one if it it does not)
            task_result = run_container_task.delay(
                user_id=user.id,
                challenge_id=challenge_id,
                image_name=image_name,
                container_id=container_id)

            # TODO: Fix this, as waiting for an async task as soon
            # as submitting defeats the purpose of Celery.
            cinfo = task_result.get()
            #print(container_info)

            if cinfo is None or cinfo['port'] is None:
                result = {
                    'workerid': None,
                    'status': _("Could not run the container! Please ask help to an administrator"),
                    'encoding': 'utf-8'
                }
                return JsonResponse(result)

            # Update UserChallengeContainer with the container id and port
            try:
                ucc = UserChallengeContainer.objects.get(
                    challenge=challenge,
                    user=user)
                ucc.container_id = cinfo['id']
                ucc.port = cinfo['port']
                ucc.save(update_fields=['container_id', 'port'])
            except UserChallengeContainer.DoesNotExist:
                ucc = UserChallengeContainer(
                    container_id=cinfo['id'],
                    challenge=challenge,
                    user=user,
                    port=cinfo['port'])
                ucc.save()
            g_logger.info("db udpated with container's id and port")

            # Prepare SSH connection

            #self.policy = policy
            #self.host_keys_settings = host_keys_settings
            self.ssh_client = self.get_ssh_client()
            #self.debug = self.settings.get('debug', False)
            #self.font = self.settings.get('font', '')
            result = {
                'workerid': None,
                'status': None,
                'encoding': None
            }

            src_ip, src_port = self.get_client_ip_and_port(request)
            #print(ip, port)
            workers = clients.get(src_ip, {})
            if workers and len(workers) >= MAXCONN:
                raise PermissionDenied(_('Too many live connections.'))

            # TODO: check origin
            #self.check_origin()

            try:
                _args = Args(
                    request,
                    cinfo['port'],
                    self.ssh_client.get_host_keys(),
                    self.ssh_client.get_system_host_keys()).get_args()
            except InvalidValueError as exc:
                return HttpResponseBadRequest(str(exc))

            future = self.executor.submit(self.ssh_connect, _args)

            try:
                 #worker = yield future
                worker = future.result()
            except (ValueError, paramiko.SSHException) as exc:
                g_logger.error(traceback.format_exc())
                result.update(status=str(exc))
            else:
                if not workers:
                    clients[src_ip] = workers
                worker.src_addr = (src_ip, src_port)
                workers[worker.gid] = worker
                self.loop.call_later(
                    RECYLE_WORKER_DELAY, recycle_worker, worker)
                result.update(
                    workerid=worker.gid, status='', encoding=worker.encoding)

            return JsonResponse(result)

        # form is not valid
        return render(
            request,
            template_name=self.template_name,
            context={'form': form})

    def upload_solution_form(self, request, *_args, **kwargs):
        """ We need to check if user has already tried and update the ProposedSolution
        if not just save this as the first one """

        form_data = request.POST

        user = form_data.get('user')
        challenge = form_data.get('challenge')
        proposed_solution = ProposedSolution.objects.get(
            user=user,
            challenge=challenge)

        if proposed_solution:
            # Update user's tries
            proposed_solution.tries = proposed_solution.tries + 1
            proposed_solution.save()

        form = UploadSolutionForm(
            form_data,
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
            #print(res.id, res.status)
            #context = super().get_context_data(**kwargs)
            context = self.get_context_data(**kwargs)
            context['task_id'] = task_id

            return self.render_to_response(context=context)

        # Form is not valid
        return render(
            request,
            template_name=self.template_name,
            context={'form': form})

    def save_container(self, request, *_args, **kwargs):
        """ save current container as a new image """

        user = request.user
        challenge_id = request.POST['challenge_id']
        challenge = Challenge.objects.get(id=challenge_id)

        # Get current container
        ucc = UserChallengeContainer.objects.get(user=user, challenge=challenge)

        if ucc.container_id:
            challenge_title = challenge.title.replace('\'', '_').replace(' ', '_')
            image_name = f"inabox_{user.username}_{challenge_title}".lower()

            res = commit_container_task.delay(
                container_id=ucc.container_id,
                image_name=image_name)

            if res:
                # Update UserChallengeImage with the new image id
                try:
                    uci = UserChallengeImage.objects.get(
                        challenge=challenge,
                        user=user)
                    uci.image_name = image_name
                    uci.save(update_fields=['image_name'])
                except UserChallengeImage.DoesNotExist:
                    uci = UserChallengeImage(
                        image_name=image_name,
                        challenge=challenge,
                        user=user)
                    uci.save()

                context = self.get_context_data(**kwargs)
                return self.render_to_response(context=context)

        # Could not save container
        g_logger.warning("Error trying to commit container [%s]", ucc.container_id)
        return render(
            request,
            template_name="app/error.html",
            context={
                'error_title': _("Save container error"),
                'error_id': 1001,
                'error_message': f"Error trying to commit container {ucc.container_id}"}
        )

    def add_comment(self, request, *_args, **kwargs):
        """ Adds new comment to challenge """
        user = request.user
        challenge_id = request.POST['challenge_id']
        challenge = Challenge.objects.get(id=challenge_id)

        # set active to True by default, if this causes problems, comments will have to be moderated
        comment = Comment(user=user, challenge=challenge, body=request.POST['body'], active=True)
        comment.save()

        context = self.get_context_data(**kwargs)
        return self.render_to_response(context=context)

    def post(self, request, *_args, **_kwargs):
        """ Deal with post data """
        # assign the object to the view
        self.object = self.get_object()

        # check that user is authenticated
        if not request.user.is_authenticated:
            raise PermissionDenied()

        if request.POST.get("form_name") == "UploadSolutionForm":
            return self.upload_solution_form(request)

        if request.POST.get("form_name") == "ChallengeSSHForm":
            return self.challenge_ssh_form(request)

        if request.POST.get("form_name") == "SaveContainerForm":
            return self.save_container(request)

        if request.POST.get("form_name") == "CommentForm":
            return self.add_comment(request)

        if request.POST.get("form_name") == "start-again":
            return self.start_again(request)

        return HttpResponseBadRequest()

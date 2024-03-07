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

class VerifyEmailView(generic.base.TemplateView):
    """ Send the verification link to the user’s email """
    template_name = 'app/verify_email/verify_email.html'

    def post(self, request):
        """ send email with verification link """
        if request.method == "POST":
            if not request.user.profile.email_is_verified:
                current_site = get_current_site(request)
                user = request.user
                email = request.user.email
                subject = "Verify Email"
                template = 'app/verify_email/verify_email_message.html'
                message = render_to_string(template, {
                    'request': request,
                    'user': user,
                    'domain': current_site.domain,
                    'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                    'token':account_activation_token.make_token(user),
                })
                email = EmailMessage(
                    subject, message, to=[email]
                )
                email.content_subtype = 'html'
                try:
                    email.send()
                except SMTPAuthenticationError as exc:
                    error_message = to_str(exc.smtp_error)
                    g_logger.warning(error_message)
                    error_message = error_message.split('\n')
                    return render(
                        request,
                        template_name="app/error.html",
                        context={
                            'error_title': _("Error sending verification email"),
                            'error_id': exc.smtp_code,
                            'error_message': error_message }
                    )
                return redirect('/verify-email-sent')
            # email is already verified
            return redirect('signup')
        return render(request, self.template_name)


class VerifyEmailSentView(generic.base.TemplateView):
    """ Email was sent. Tell the user to check his/her email """
    template_name = 'app/verify_email/verify_email_sent.html'


class VerifyEmailConfirmView(generic.base.TemplateView):
    """ Gets verification link and verifies it """
    template_name = 'app/verify_email/verify_email_confirm.html'

    def get(self, request, *args, **kwargs):

        uidb64 = kwargs.get('uidb64')
        token = kwargs.get('token')

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.profile.email_is_verified = True
            user.profile.save()
            messages.success(request, 'Your email has been verified.')
            return redirect('/verify-email-complete')
        messages.warning(request, 'The link is invalid.')
        return render(request, 'app/verify_email/verify_email_confirm.html')


class VerifyEmailCompleteView(generic.base.TemplateView):
    """ redirect the user to our website after verification """
    template_name = 'app/verify_email/verify_email_complete.html'

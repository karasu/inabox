""" Celery. Create your tasks here """

import json
import tarfile
import os
import stat
import uuid

from django.utils.translation import gettext_lazy as _

import pika
import docker

from celery import shared_task
from celery.utils.log import get_task_logger
from celery_progress.backend import ProgressRecorder

from .models import Challenge, ProposedSolution
#from .models import UserChallengeContainer

g_logger = get_task_logger(__name__)

class ValidateSolution():
    """ Validate user's solution to a challenge """
    _STEPS = 5

    def __init__(self, proposed_solution_id):
        """ Initalise class properties """
        self._client = None

        # store proposed solution id for reference
        self.proposed_solution_id = proposed_solution_id

        # Create the progress recorder instance
        # which we'll use to update the web page
        self._progress_recorder = ProgressRecorder(self)
        self._step = 1

        # docker container instance
        self._container = None

    def connect(self):
        """ Connect to docker and check it is running """
        self._client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        self._client.ping()

    def run_container(self, docker_image_name):
        """ Run a docker container from the challenge image and
        maintain it running using the tail command """
        cmd = ["tail", "-f", "/dev/null"]
        self._container = self._client.containers.run(
            image=docker_image_name,
            command=cmd,
            detach=True)

    def progress(self, description):
        """ Update progress bar """
        self._progress_recorder.set_progress(
            self._step, self._STEPS, description=description)

        if self._step < self._STEPS:
            self._step = self._step + 1

    def copy_file(self, file_path):
        """ Copies file inside the container. It uses tar to
         be able to use docker put_archive function """

        os.chmod(file_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        tar_path = file_path + '.tar'
        with tarfile.open(tar_path, mode='w') as tar:
            tar.add(file_path)

        # Copy contents of tar file inside our container with put_archive
        with open(tar_path, 'rb') as tar_fd:
            res = self._container.put_archive(path='/', data=tar_fd)
        if not res:
            raise docker.errors.APIError(f"Cannot put {tar_path} inside the container")

    def run_script(self, path):
        """ run script inside the container """

        # source file containing a ' in its name will mess it up
        path = "'" + path.replace("'", "'\\''") + "'"

        # run script
        cmd = ["/bin/sh", "-c", path]
        exit_code, output = self._container.exec_run(
            cmd=cmd,
            user="inabox")

        if output:
            output = output.decode("utf-8")

        return exit_code, output

    def delete_container(self):
        """ Stop and delete the container (this takes a bit...) """
        self._container.stop()
        self._container.remove()

    def run(self):
        """ run task """

        # Get proposed solution and challenge
        proposed_solution = ProposedSolution.objects.get(
            id=self.proposed_solution_id)
        challenge = Challenge.objects.get(
            id=proposed_solution.challenge.id)

        scripts = [
            proposed_solution.script.path,
            challenge.check_solution_script.path]


        # Get challenge docker image name
        docker_image_name = challenge.docker_image.docker_name

        self.progress("Checking docker image...")

        try:
            # Connect to docker and check docker image
            self.connect()
            self._client.images.get(docker_image_name)

            self.progress(_("Creating container..."))
            self.run_container(docker_image_name)

            self.progress(_("Copying scripts inside the container..."))
            for script in scripts:
                self.copy_file(script)

            self.progress(_("Running proposed solution..."))
            exit_code, output = self.run_script(proposed_solution.script.path)
            if output:
                g_logger.warning(output)

            self.progress(_("Checking proposed solution..."))
            exit_code, output = self.run_script(challenge.check_solution_script.path)

            if output is None:
                raise docker.errors.APIError(_("Did not get any output from the check script"))

            g_logger.warning(output)

            proposed_solution.is_tested = True
            proposed_solution.last_test_result = output.decode("utf-8")

            if exit_code == 0:
                # Seems that proposed solution works!
                proposed_solution.is_solved = True
                g_logger.warning(
                    "%s has been solved by %s!",
                    challenge.title, proposed_solution.user.username)

                challenge.solved = challenge.solved + 1
                challenge.save()

            proposed_solution.save()

            self.progress(_("Removing testing container..."))
            self.delete_container()

        except docker.errors.ImageNotFound:
            g_logger.error("Docker image %s not found", docker_image_name)
            return False, f"Docker image {docker_image_name} not found"
        except (docker.errors.APIError, FileNotFoundError) as exc:
            g_logger.error(exc)
            return False, str(exc)

        return True, _("Task complete")

@shared_task(bind=True)
def validate_solution_task(proposed_solution_id):
    """ Check if proposed solution is right or wrong """

    return ValidateSolution(proposed_solution_id).run()


class Switchboard():
    """ Listen to switchboard messages through rabbitmq (consumer) """

    QUEUE = "switchboard"

    def __init__(self):
        self._connection = None
        self._channel = None

        self.response = None
        self.corr_id = None
        self.callback_queue = None

    def connect(self):
        """ Connect to rabbitmq """

        credentials = pika.PlainCredentials('guest', 'guest')

        parameters = pika.ConnectionParameters(
                host='localhost',
                port=5672,
                virtual_host='/',
                heartbeat=5,
                credentials=credentials
            )

        return pika.BlockingConnection(parameters)

    def on_response(self, ch, method, props, body):
        """ Receives switchboard response"""
        if self.corr_id == props.correlation_id:
            self.response = body
            g_logger.debug("Response from switchboard: %s", body)

    def setup_channel(self):
        """ setup rabbitmq channel """
        channel = self._connection.channel()

        result = channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

        return channel

    def close(self):
        """ closes the connection """
        if self._connection is not None:
            self._connection.close()

    def run(self, call):
        """ Setup connection and make the rpc call """
        self._connection = self.connect()
        self._channel = self.setup_channel()

        # Asks switchboard to create a new container
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self._channel.basic_publish(
            exchange='',
            routing_key='rpc_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=json.dumps(call))

        self._connection.process_data_events(time_limit=None)

        return self.response


@shared_task(bind=True)
def switchboard_task(task, user_id, challenge_id, docker_image_name):
    """ Listen to switchboard messages """
    g_logger.debug(
        "[] User %d is asking switchboard for a new container for challenge [%d]",
        user_id, challenge_id)

    call = {
            "docker_instance_id": 0,
            "docker_options": "",
            "docker_image_name": image_name,
            "user_id": user_id,
            "challenge_id": challenge_id,
            "port": 0,
            "error": None
         }

    switchboard = Switchboard()
    return switchboard.run(call)

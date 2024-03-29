""" Celery. Create your tasks here """

import tarfile
import os
import stat

import docker

from django.utils.translation import gettext_lazy as _

from celery import shared_task
from celery.utils.log import get_task_logger
from celery_progress.backend import ProgressRecorder
from inabox.celery import app as celery_app

from .models import Challenge, ProposedSolution
from .models import UserChallengeContainer

from .container import Container, Image

# connection url to the docker service
URL = "unix://var/run/docker.sock"

g_logger = get_task_logger(__name__)

class ValidateSolution():
    """ Validate user's solution to a challenge """
    _STEPS = 5

    def __init__(self, task, proposed_solution_id):
        """ Initalise class properties """
        self._client = None

        # store proposed solution id for reference
        self.proposed_solution_id = proposed_solution_id

        # Create the progress recorder instance
        # which we'll use to update the web page
        self._progress_recorder = ProgressRecorder(task)
        self._step = 1

        # docker container instance
        self._container = None

    def connect(self):
        """ Connect to docker and check it is running """
        self._client = docker.DockerClient(base_url=URL)
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
def validate_solution_task(self, proposed_solution_id):
    """ Check if proposed solution is right or wrong """

    return ValidateSolution(self, proposed_solution_id).run()


@shared_task(bind=True)
def run_container_task(
    _self, user_id, challenge_id, image_name, container_id=None):
    """ Runs docker container """

    if container_id is None:
        g_logger.info(
            "User [%d] is asking for a new container for challenge [%s]",
            user_id, challenge_id)
    else:
        g_logger.info(
            "User [%d] is trying to reuse container [%s] for challenge [%s]",
            user_id, container_id, challenge_id)

    container = Container(container_id)
    res = container.run(image_name)

    if res:
        g_logger.info(
            "Container [%s] is listening at port [%d]",
            container.get_id(), container.get_port())

        return {
            'id': container.get_id(),
            'port': container.get_port()}

    # Could not start the container.
    g_logger.warning(
      "Couldn't create (or reuse) container for challenge [%s] asked by user [%s]",
            challenge_id, user_id)
    return None


@shared_task(bind=True)
def remove_container_task(_self, container_id):
    """ Removes docker container """

    container = Container(container_id)
    if container.exists():
        container.remove()
        g_logger.warning("Container [%s] removed", container_id)
    else:
        g_logger.warning("Could not remove [%s] container", container_id)

@shared_task(bind=True)
def remove_image_task(_self, image_name):
    """ Removes docker image """

    image = Image(image_name)
    if image.is_ok():
        image.remove()
        g_logger.warning("Docker image [%s] removed", image_name)


@shared_task(bind=True)
def commit_container_task(_self, container_id, image_name):
    """ Saves container as a new image """
    container = Container(container_id)

    g_logger.info("Saving container [%s] as [%s]", container_id, image_name)
    return container.commit(image_name)


@celery_app.task
def prune_dead_containers():
    """ This task removes all stoped containers!!! """

    g_logger.info(
        "Prunning all stoped containers references in UserChallengeContainer table...")

    uccs = UserChallengeContainer.objects.all()

    for ucc in uccs:
        cid = ucc.container_id
        container = Container(container_id=cid)
        if container.status() != "running":
            ucc.delete()
            g_logger.warning("Container [%s] reference has been removed from database", cid)
            container.remove()
            g_logger.warning("Container [%s] has been removed from Docker", cid)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **_kwargs):
    """ Put periodic tasks here """

    # Calls prune_dead_containers every two minutes.
    sender.add_periodic_task(2*60.0, prune_dead_containers)

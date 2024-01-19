""" Celery. Create your tasks here """

import logging
import tarfile
import os
import stat

from django.utils.translation import gettext_lazy as _

from celery import shared_task
from celery_progress.backend import ProgressRecorder

import docker

from .models import Challenge, ProposedSolution

class ValidateSolution():
    def __init__(self, proposed_solution_id):
        self.proposed_solution_id = proposed_solution_id

    def run(self):
        # Create the progress recorder instance
        # which we'll use to update the web page
        progress_recorder = ProgressRecorder(self)

        # Get proposed solution and challenge
        proposed_solution = ProposedSolution.objects.get(
            id=self.proposed_solution_id)
        challenge = Challenge.objects.get(
            id=proposed_solution.challenge.id)

        # Get challenge docker image name
        docker_image_name = challenge.docker_image.docker_name

        progress_recorder.set_progress(1, 4, description="Checking docker image...")

        # Connect to docker and check it is running
        try:
            docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')
            docker_client.ping()
        except docker.errors.APIError as err:
            logging.error(err)
            return False, str(err)

        # Check docker image
        try:
            docker_client.images.get(docker_image_name)
        except docker.errors.ImageNotFound:
            logging.error("Docker image %s not found", docker_image_name)
            return False, f"Docker image {docker_image_name} not found"
        except docker.errors.APIError as err:
            logging.error(err)
            return False, str(err)

        progress_recorder.set_progress(2, 4, description="Creating container...")

        # Run a docker container from the challenge image and maintain it
        # running using the tail command
        try:
            cmd = ["tail", "-f", "/dev/null"]
            container = docker_client.containers.run(
                image=docker_image_name,
                command=cmd,
                detach=True)
        except docker.errors.APIError as err:
            logging.error(err)
            return False, str(err)

        # Create a tar file for each script (so we can put them inside our container)
        scripts = [
            proposed_solution.script.path,
            challenge.check_solution_script.path]

        for script in scripts:
            try:
                os.chmod(script, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            except FileNotFoundError as err:
                logging.error(err)
                return False, str(err)

            tar_path = script + '.tar'
            with tarfile.open(tar_path, mode='w') as tar:
                tar.add(script)

            # Copy contents of tar file inside our container with put_archive
            try:
                with open(tar_path, 'rb') as tar_fd:
                    res = container.put_archive(path='/', data=tar_fd)
                if not res:
                    logging.error(
                        "put_archive failed. Cannot put %s contents inside the container",
                        tar_path)
                    return (
                        False,
                        f"put_archive failed. Cannot put {tar_path} contents inside the container")
            except docker.errors.APIError as err:
                logging.error(err)
                return False, str(err)

        progress_recorder.set_progress(3, 4, description="Checking proposed solution...")

        # Run the user's proposed solution script in the container
        try:
            # source file containing a ' in its name will mess it up
            script = proposed_solution.script.path
            script = "'" + script.replace("'", "'\\''") + "'"
            cmd = ["/bin/sh", "-c", script]
            exit_code, output = container.exec_run(
                cmd=cmd,
                user="inabox")
        except docker.errors.APIError as err:
            logging.error(err)
            return False, str(err)

        if output:
            logging.warning(output.decode("utf-8"))

        # Now run the challenge solution check script to test if the proposed
        # solution has worked or not
        try:
            # source file containing a ' in its name will mess it up
            script = challenge.check_solution_script.path
            script = "'" + script.replace("'", "'\\''") + "'"
            cmd = ["/bin/sh", "-c", script]
            exit_code, output = container.exec_run(
                cmd=cmd,
                user="inabox")
        except docker.errors.APIError as err:
            logging.error(err)
            return False, str(err)

        if output is None:
            err = _("Did not get any output from the check script")
            return False, str(err)

        logging.warning(output.decode("utf-8"))

        proposed_solution.is_tested = True
        proposed_solution.last_test_result = output.decode("utf-8")

        if exit_code == 0:
            # Seems that proposed solution works!
            proposed_solution.is_solved = True
            logging.warning(
                "%s has been solved by %s!",
                challenge.title, proposed_solution.user.username)

            challenge.solved = challenge.solved + 1
            challenge.save()
        #else:
        #    # Proposed solution does not work
        #    proposed_solution.is_solved = False

        proposed_solution.save()

        progress_recorder.set_progress(4, 4, description="Deleting test container...")

        # Stop and delete the container (this takes a long time...)
        try:
            container.stop()
            container.remove()
        except docker.errors.APIError as err:
            logging.error(err)
            return False, str(err)

        return True, _("Task complete")

@shared_task(bind=True)
def validate_solution_task(self, proposed_solution_id):
    """ Check if proposed solution is right or wrong """

    return ValidateSolution(proposed_solution_id).run()


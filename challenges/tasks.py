# Celery
# Create your tasks here

from django.utils.translation import gettext_lazy as _

from .models import ProposedSolution, Challenge

from celery import shared_task

import docker
import logging
import tarfile
import os
import stat
import tempfile

@shared_task
def validate_solution_task(proposed_solution_id):

    # Get proposed solution and challenge
    proposed_solution = ProposedSolution.objects.get(id=proposed_solution_id)
    challenge = Challenge.objects.get(id=proposed_solution.challenge.id)

    # Get challenge docker image name
    docker_image_name = challenge.docker_image.docker_name

    # Connect to docker and check it is running
    try:
        docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        docker_client.ping()
    except docker.errors.APIError as err:
        logging.error(err)
        return False

    # Check docker image
    try:
        docker_image = docker_client.images.get(docker_image_name)
    except docker.errors.ImageNotFound:
        logging.error("Docker image {} not found".format(docker_image_name))
        return False
    except docker.errors.APIError as err:
        logging.error(err)
        return False
    
    # Run a docker container from the challenge image and maintain ir
    # running with tail command
    try:
        cmd = ["tail", "-f", "/dev/null"]
        container = docker_client.containers.run(
            image=docker_image_name,
            command=cmd,
            detach=True)
    except docker.errors.APIError as err:
        logging.error(err)
        return False

    # Create a tar file for each script (so we can put them inside our container)    
    scripts = [
        proposed_solution.script.path,
        challenge.check_solution_script.path]

    for script in scripts:
        # FIXME: Obviously not a good thing to do
        os.chmod(script, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        tar_path = script + '.tar'
        with tarfile.open(tar_path, mode='w') as tar:
            tar.add(script)

        # Copy contents of tar file inside our container with put_archive
        try:
            with open(tar_path, 'rb') as fd:
                res = container.put_archive(path='/', data=fd)
            if not res:
                logging.error("put_archive failed. Cannot put {} contents inside the container".format(tar_path))
                return False
        except docker.errors.APIError as err:
            logging.error(err)
            return False
    
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
        return False 

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
        return False 

    if output:
        logging.warning(output.decode("utf-8"))

    if output is None:
        logging.error(_("Did not get any output from the check script"))
        return False
    else:
        proposed_solution.is_tested = True
        proposed_solution.last_test_result = output.decode("utf-8")
        
        if exit_code == 0:
            # Seems that proposed solution works!
            proposed_solution.is_solved = True
            logging.warning("{} has been solved by {}!".format(
                challenge.title, proposed_solution.user.username))

            challenge.times_solved = challenge.times_solved + 1
            challenge.save()
        #else:
        #    # Proposed solution does not work
        #    proposed_solution.is_solved = False
        
        proposed_solution.save()

    # Stop and delete the container (this takes a long time...)
    try:
        container.stop()
        container.remove()
    except docker.errors.APIError as err:
        logging.error(err)
    
    return True

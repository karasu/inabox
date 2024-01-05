# Celery
# Create your tasks here

from .models import ProposedSolution, Challenge

from celery import shared_task

import docker
import logging


@shared_task
def validate_solution_task(proposed_solution_id):

    # Get proposed solution and challenge
    proposed_solution = ProposedSolution.objects.get(id=proposed_solution_id)
    challenge = Challenge.objects.get(id=proposed_solution.challenge.id)

    # Get proposed solution and challenge solution scripts
    '''
    try:
        with proposed_solution.script.open('r') as f:
            proposed_solution_script = f.readlines()

        with challenge.check_solution_script.open('r') as f:
            challenge_solution_script = f.readlines()
    except FileNotFoundError as err:
        logging.error(err)
        return False
    '''

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
    
    # Run a docker container from the challenge image
    try:
        container = docker_client.containers.run(
            image=docker_image_name,
            command="/bin/sh",
            detach=True)
    except docker.errors.APIError as err:
        logging.error(err)
        return False
    
    # Run the user's proposed solution script in the container
    try:
        cmd = ["/bin/sh", "-c", proposed_solution.script.path]
        exit_code, output = container.exec_run(cmd, demux=True)
    except docker.errors.APIError as err:
        logging.error(err)
        return False 

    # Now run the challenge solution check script to test if the proposed
    # solution has worked or not
    try:
        cmd = ["/bin/sh", "-c", challenge_solution.script.path]
        exit_code, output = container.exec_run(cmd, demux=True)
    except docker.errors.APIError as err:
        logging.error(err)
        return False 

    (stdout, _) = output

    logging.info(stdout)

    proposed_solution.is_tested = True
    proposed_solution.last_test_result = stdout.decode("utf-8")

    if exit_code == 0:
        # Seems that proposed solution works!
        proposed_solution.is_solved = True
    else:
        # Proposed solution does not work.
        proposed_solution.is_solved = False
    
    proposed_solution.save()

    return True

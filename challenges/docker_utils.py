""" Docker helper functions """

import docker

from .logger import g_logger

# connection url to the docker service
URL = "unix://var/run/docker.sock"

def container_exists(container_id):
    """ Check if docker container exists """

    # get docker client
    client = docker.DockerClient(base_url=URL)

    if client:
        try:
            _ = client.get(container_id)
            return True
        except docker.errors.NotFound:
            return False
    return False

def container_stopped(container_id):
    """ Check if docker container exists and if it is stopped """
    # get docker client
    client = docker.DockerClient(base_url=URL)

    if client:
        try:
            container = client.get(container_id)
        except docker.errors.NotFound:
            return False

        if container.status == "stopped":
            return True
    return False

def container_running(container_id):
    """ Check if docker container exists and if it is running """

    # get docker client
    client = docker.DockerClient(base_url=URL)

    if client:
        try:
            container = client.get(container_id)
        except docker.errors.NotFound:
            return False

        if container.status == "running":
            return True
    return False

def run_container(image_name, options):
    """ Runs a new detached container from image name and returns it """

    # force detached option
    options['detach'] = True

    # get docker client
    client = docker.DockerClient(base_url=URL)

    if client:
        try:
            # if detached, run returns the container itself
            return client.containers.run(image=image_name, **options)
        except docker.errors.ContainerError:
            g_logger.warning(
                "Coudn't start a new container from image %s", image_name)
        except docker.errors.ImageNotFound:
            g_logger.warning(
                "Docker image %s does not exist", image_name)
        except docker.errors.APIError as exc:
            g_logger.warning(
                "Error running a container from image %s: %s", image_name, exc)

    return False

""" Docker helper functions """

import docker

from .logger import g_logger

# connection url to the docker service
URL = "unix://var/run/docker.sock"

class DockerContainer():
    """ Represents a docker container """

    def __init__(self, container_id=None):
        self._container = None

        if container_id is not None:
            client = docker.DockerClient(base_url=URL)

            if client:
                try:
                    self._container = client.get(container_id)
                except docker.errors.NotFound:
                    g_logger.warning("Container with id %s not found", container_id)

    def exists(self):
        """ Check if container exists """
        if self._container:
            return True
        return False

    def status(self):
        """ Get container's current status """
        if self._container:
            return self._container.status
        return None

    def stop(self):
        """ Stop container """
        if self._container:
            self._container.stop()

    def get_instance(self):
        """ return container instance """
        return self._container

    def run(self, image_name, options):
        """ Runs a new detached container from image name and returns it """

        # force detached option
        options['detach'] = True

        # get docker client
        client = docker.DockerClient(base_url=URL)

        if client:
            try:
                # if detached, run returns the container itself
                self._container = client.containers.run(
                    image=image_name, **options)
            except docker.errors.ContainerError:
                g_logger.warning(
                    "Coudn't start a new container from image %s", image_name)
            except docker.errors.ImageNotFound:
                g_logger.warning(
                    "Docker image %s does not exist", image_name)
            except docker.errors.APIError as exc:
                g_logger.warning(
                    "Error running a container from image %s: %s", image_name, exc)


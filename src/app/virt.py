""" Docker helper functions """

import socket
import time

import libvirt
import sys

from .logger import g_logger


class Image():
    """ Represents a docker image """
    def __init__(self, name=None):
        self._image = None
        self._name = None
        self._client = docker.DockerClient(base_url=URL)
        if not self._client:
            g_logger.error("Cannot connect to docker service. Is it running?")
        elif name:
            self._name = name
            try:
                self._image = self._client.images.get(name)
            except docker.errors.ImageNotFound:
                self._image = None
                g_logger.warning("Could not find docker image named %s", name)
            except docker.errors.APIError as exc:
                g_logger.warning(exc)

    def is_ok(self):
        """ Returns True if a docker image has been loaded """
        if self._image:
            return True
        return False

    def remove(self, name=None, force=True, noprune=True):
        """ Removes an image """
        if self._image:
            if name is None:
                name = self._name
            self._client.images.remove(image=name, force=force, noprune=noprune)
            self._image = None
            self._name = None


class Container():
    """ Represents a docker container """

    def __init__(self, container_id=None):
        self._container = None
        self._client = docker.DockerClient(base_url=URL)
        self._port = None

        if self._client:
            if container_id:
                # Get the container
                try:
                    self._container = self._client.containers.get(container_id)
                    if self._container:
                        ports = self._container.attrs["NetworkSettings"]["Ports"]
                        self._port = int(ports["22/tcp"][0]["HostPort"])
                except (docker.errors.NotFound, KeyError, AttributeError):
                    # TODO: reuse container even if it is stopped
                    g_logger.warning(
                        "Container with id [%s] not found or is not running",
                        container_id)
                    self._container = None
        else:
            g_logger.error("Cannot connect to docker service. Is it running?")

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

    def start(self):
        """ Start existing container """
        if self._container:
            self._container.start()

    def stop(self):
        """ Stop container """
        if self._container:
            self._container.stop()

    def wait(self):
        """ Wait for container to stop """
        if self._container:
            self._container.wait()

    def get_instance(self):
        """ returns container instance """
        return self._container

    def get_id(self):
        """ returns container id """
        if self._container:
            return self._container.id
        return None

    def get_name(self):
        """ returns container name """
        if self._container:
            return self._container.name
        return None

    def get_port(self):
        """ Returns container's ssh outer port """
        return self._port

    def get_info(self):
        """ Returns a dict with container's info """
        return {
            "id": self.get_id(),
            "name": self.get_name(),
            "port": self.get_port() }

    def run(self, image_name=None):
        """ Runs a new detached container from image name """

        if not self._client:
            return False

        if self._container:
            # container already exists, let's simply start it
            self.start()
            g_logger.info("container already exists, let's simply start it")
            return self.get_info()

        # Ok, container does not exist, we need to create it from image_name

        if image_name is None:
            g_logger.warning(
                "No docker image name has been provided and no previous container was found.")
            return False

        # Expose port 22 to this port
        self._port = self.get_free_port()

        options = { 'detach': True, 'ports': {22: self._port}}

        try:
            # if detached, run returns the container itself
            self._container = self._client.containers.run(
                image=image_name, **options)

            #self.wait_for_running()

            cname = self.get_name()
            cid = self.get_id()

            # wait for container external port
            if self._port and self._wait_for_open_port(port=self._port):
                g_logger.info(
                    "Port %d of started container [%s] with ID [%s] is OPEN :)",
                    self._port, cname, cid)
                return self.get_info()

            g_logger.warning(
                "Port %d of started container %s with ID [%s] is CLOSED :(",
                self._port, cname, cid)
        except docker.errors.ContainerError:
            g_logger.warning("Coudn't start a new container from image %s", image_name)
        except docker.errors.ImageNotFound:
            g_logger.warning("Docker image %s does not exist", image_name)
        except docker.errors.APIError as exc:
            g_logger.warning("Error running a container from image %s: %s", image_name, exc)

        return None

    def get_free_port(self):
        """ Gets a free tcp port """
        sock = socket.socket()
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        return port

    def _is_port_open(self, port, read_timeout=0.1):
        """ check if port is open """
        sock = socket.socket()
        ret = False

        if port is None:
            time.sleep(read_timeout)
        else:
            try:
                sock.connect(("0.0.0.0", port))
                # just connecting is not enough, we should try to read
                # and get at least 1 byte back since the daemon in the
                # container might not have started accepting
                # connections yet
                sock.settimeout(read_timeout)
                data = sock.recv(1)
                ret = len(data) > 0
            except socket.error:
                ret = False

        sock.close()
        return ret

    def _wait_for_open_port(self, port, timeout=5, step=0.1):
        """ waits for open port """
        started = time.time()
        while started + timeout >= time.time():
            if self._is_port_open(port):
                return True
            time.sleep(step)
        return False

    def wait_for_running(self):
        """ waits until container status is running or until times out"""
        timeout = 120
        stop_time = 3
        elapsed_time = 0
        while self._container.status != 'running' and elapsed_time < timeout:
            time.sleep(stop_time)
            elapsed_time += stop_time
            self._container.reload()
            continue

    def commit(self, image_name):
        """ Commit a container to create an image called 'name' from its contents """
        # commit(repository=None, tag=None, **kwargs)
        # Commit a container to an image. Similar to the docker commit command.
        # Parameters:
        # repository (str) – The repository to push the image to
        # tag (str) – The tag to push
        # message (str) – A commit message
        # author (str) – The name of the author
        # pause (bool) – Whether to pause the container before committing
        # changes (str) – Dockerfile instructions to apply while committing
        # conf (dict) – The configuration for the container. See the
        #      Engine API documentation for full details.
        # Raises:
        # docker.errors.APIError – If the server returns an error.

        # Note: Overwrites image if it already exists
        try:
            self._container.stop()
            self._container.wait()
            self._container.commit(repository=image_name, tag="latest")
            g_logger.info("Container commited as %s", image_name)
            return True
        except docker.errors.APIError as exc:
            g_logger.warning(exc)
            return False

    def remove(self, volumes=True, link=False, force=False):
        """ Remove this container. Similar to the docker rm command. """
        # Parameters:
        # v (bool) – Remove the volumes associated with the container
        # link (bool) – Remove the specified link and not the underlying container
        # force (bool) – Force the removal of a running container (uses SIGKILL)

        try:
            if self._client and self._container:
                self._container.remove(v=volumes, link=link, force=force)
                return True
        except docker.errors.APIError as exc:
            g_logger.warning(exc)
        return False

""" Docker helper functions """

import socket
import time
import pprint

import docker

from .logger import g_logger

# connection url to the docker service
URL = "unix://var/run/docker.sock"

class Container():
    """ Represents a docker container """

    def __init__(self, container_id=None):
        self._container = None
        self._client = docker.DockerClient(base_url=URL)

        if self._client:
            if container_id:
                # Get the container
                try:
                    self._container = self._client.get(container_id)
                except docker.errors.NotFound:
                    g_logger.warning("Container with id %s not found", container_id)
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

    def get_port(self, opt_port=None):
        """ Returns container's ssh outer port """
        if self._container:
            try:
                return int(
                self._container.attrs['NetworkSettings']['Ports']['22/tcp'][0]['HostPort'])
            except (AttributeError, KeyError) as exc:
                g_logger.warning("Failed to get port information: %s", exc)
                return opt_port
        return None

    def run(self, image_name=None, options=None):
        """ Runs a new detached container from image name and returns it """

        if not self._client:
            return None

        if self._container:
            # container already exists, let's simply start it
            self.start()
            return {
                "id": self.get_id(),
                "name": self.get_name(),
                "port": self.get_port() }

        # Ok, container does not exist, we need to create it from image_name

        if image_name is None:
            g_logger.warning(
                "No docker image name has been provided and no previous container was found.")
            return None

        if options is None:
            g_logger.warning(
                "No docker options have been provided and no previous container was found.")
            return None

        # force detached option
        options['detach'] = True

        g_logger.warning("Starting a NEW container with these options: %s",
            pprint.pformat(options))

        try:
            # if detached, run returns the container itself
            self._container = self._client.containers.run(
                image=image_name, **options)

            cid = self.get_id()
            cname = self.get_name()
            cport = options['ports'][22]

            # wait until container is available
            if self._wait_for_open_port(port=cport):
                g_logger.info(
                    "Port %d of started container [%s] with ID [%s] is OPEN :)",
                    cport, cname, cid)
                return { "id": cid, "name": cname, "port": cport }
        except docker.errors.ContainerError:
            g_logger.warning("Coudn't start a new container from image %s", image_name)
        except docker.errors.ImageNotFound:
            g_logger.warning("Docker image %s does not exist", image_name)
        except docker.errors.APIError as exc:
            g_logger.warning("Error running a container from image %s: %s", image_name, exc)

        g_logger.warning(
            "Port %d of started container %s with ID [%s] is CLOSED :(",
            cport, cname, cid)

        return None

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

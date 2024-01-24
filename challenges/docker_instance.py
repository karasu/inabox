""" docker instance module """

import pprint
import socket
import time

import docker

from celery.utils.log import get_task_logger

g_logger = get_task_logger(__name__)


class DockerInstance():
    """ this class represents a single docker instance listening on a certain middleport.
    The middleport is managed by the DockerPorts global object
    After the docker container is started, we wait until the middleport becomes reachable
    before returning """

    def __init__(self, image_name, docker_options, outer_port):
        self.image_name = image_name
        self.docker_options = docker_options
        self.outer_port = outer_port
        self._instance = None

    def get_instance_id(self):
        """ get instance id """
        if self._instance is None:
            g_logger.warning("Container is not running. Did you call start()?")
            return None
        try:
            return self._instance.id
        except Exception as exc:
            g_logger.warning("Failed to get instance id: %s", exc)
        return None

    def get_instance_name(self):
        """ get container's name """
        if self._instance is None:
            g_logger.warning("Container is not running. Did you call start()?")
            return None
        try:
            return self._instance.name
        except Exception as exc:
            g_logger.warning("Failed to get instance name: %s", exc)
            return None

    def get_port(self):
        """ gets outer port """
        return self.outer_port

    def start(self):
        """ Start this instance """

        # get docker client
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        client.ping()

        g_logger.info("DOCKER CLIENT %s", client)

        # start instance
        try:
            g_logger.info("Starting container instance of image %s with dockeroptions %s",
                self.image_name,
                pprint.pformat(self.docker_options))

            result = client.containers.run(
                image=self.image_name,
                detach=True)
                #self.docker_options)

            self._instance = client.containers.get(result.id)

            g_logger.info("Done starting instance [%s] of container image %s",
                self.get_instance_id(), self.image_name)
        except Exception as exc:
            g_logger.warning("Failed to start an instance of image %s: %s",
                self.image_name, exc)
            self.stop()
            return False

        # wait until container is available
        g_logger.info("Started instance on port %s with ID [%s]",
            self.outer_port, self.get_instance_id())

        if self._wait_for_open_port(self.outer_port):
            g_logger.info("Port %d of started instance [%s] with ID [%s] is OPEN",
                self.outer_port, self.get_instance_name(), self.get_instance_id())
            return True

        g_logger.warning("Port %d of started instance %s with ID [%s] is CLOSED. Aborting...",
            self.outer_port, self.get_instance_name(), self.get_instance_id())
        self.stop()
        return False

    def stop(self):
        """ stop docker instance """

        cid = self.get_instance_id()
        g_logger.info("Killing and removing [%s] (port %d)", cid, self.outer_port)

        try:
            self._instance.remove(force=True)
        except Exception as exc:
            g_logger.warning(
                "Failed to remove instance [%s]: %s",
                cid, exc)
            return False
        return True

    def _is_port_open(self, port, readtimeout=0.1):
        sock = socket.socket()
        ret = False

        if port is None:
            time.sleep(readtimeout)
        else:
            try:
                sock.connect(("0.0.0.0", port))
                # just connecting is not enough, we should try to read and get at least 1 byte
                # back since the daemon in the container might not have started accepting
                # connections yet, while docker-proxy does
                sock.settimeout(readtimeout)
                data = sock.recv(1)
                ret = len(data) > 0
            except socket.error:
                ret = False

        sock.close()
        return ret

    def _wait_for_open_port(self, port, timeout=5, step=0.1):
        """ waits until instance is running """

        g_logger.info("Checking whether port %d is open...", port)

        started = time.time()

        while started + timeout >= time.time():
            if self._is_port_open(port):
                g_logger.info("Port %d is open!", port)
                return True
            time.sleep(step)
        g_logger.warning("Port %d is closed!", port)
        return False

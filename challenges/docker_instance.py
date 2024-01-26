""" docker instance module """

import pprint
import socket
import time

from celery.utils.log import get_task_logger

from .docker_utils import DockerContainer

g_logger = get_task_logger(__name__)


class DockerInstance():
    """ this class represents a single docker instance """

    # All images have to expose port 22 (ssh)
    INNER_PORT = 22

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

        if "ports" not in self.docker_options:
            self.docker_options["ports"] = {}
        self.docker_options["ports"][self.INNER_PORT] = self.outer_port

        # start instance
        container = DockerContainer()
        container.run(self.image_name, self.docker_options)

        if not container:
            g_logger.warning("Failed to start an instance of image %s",
                self.image_name)
            return False

        #self._instance = client.containers.get(result.id)
        self._instance = container.get_instance()

        g_logger.info(
            "Started container of image %s with docker_options %s",
            self.image_name,
            pprint.pformat(self.docker_options))

        cid = self.get_instance_id()
        cname = self.get_instance_name()
        cport = self.get_port()

        # wait until container is available
        g_logger.info("Started instance [%s] on port %s.", cid, cport)

        if self._wait_for_open_port(port=cport):
            g_logger.info(
                "Port %d of started instance [%s] with ID [%s] is OPEN",
                cport, cname, cid)
            return True

        g_logger.warning(
            "Port %d of started instance %s with ID [%s] is CLOSED. Aborting...",
            cport, cname, cid)

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

    def _is_port_open(self, port, read_timeout=0.1):
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
        """ waits until instance is running """
        started = time.time()

        while started + timeout >= time.time():
            if self._is_port_open(port):
                return True
            time.sleep(step)
        return False

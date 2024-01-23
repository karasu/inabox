""" docker instance module """

import pprint
import socket
import time

import docker

from logger import g_logger


class DockerInstance():
    """ this class represents a single docker instance listening on a certain middleport.
    The middleport is managed by the DockerPorts global object
    After the docker container is started, we wait until the middleport becomes reachable
    before returning """

    def __init__(self, image_name, docker_options):
        self.image_name = image_name
        self.docker_options = docker_options
        self._innerport = innerport
        self._checkupport = checkupport
        self._instance = None


    def get_mapped_port(self, in_port):
        """ return container mapped port """
        try:
            return int(
                self._instance.attrs["NetworkSettings"]["Ports"][f"{in_port}/tcp"][0]["HostPort"])
        except Exception as exc:
            g_logger.warning(
                "Failed to get port information for port %d from %d: %s",
                in_port, self.get_instance_id(), exc)
        return None

    def get_middle_port(self):
        """ returns inner port """
        return self.get_mapped_port(self._innerport)

    def get_middle_checkup_port(self):
        """ gets checkup port """
        return self.get_mapped_port(self._checkupport)

    def get_instance_id(self):
        """ get instance id """
        try:
            return self._instance.id
        except Exception as exc:
            g_logger.warning("Failed to get instance id: %s", exc)
        return "None"

    def start(self):
        """ Start this instance """

        # get docker client
        client = docker.from_env()

        # start instance
        try:
            g_logger.debug("Starting container instance of image %s with dockeroptions %s",
                self.image_name,
                pprint.pformat(self.docker_options))

            clientres = client.containers.run(
                self.image_name, **self.docker_options)

            self._instance = client.containers.get(clientres.id)


####################################### WIP


            g_logger.debug("Done starting instance %s of container image %s",
                self.image_name(), self.get_container_name())
        except Exception as exc:
            g_logger.debug("Failed to start instance %s of container %s: %s",
                self.get_profile_name(), self.get_container_name(), exc)
            self.stop()
            return False

        # wait until container's checkupport is available
        g_logger.debug("Started instance on middleport %s with ID %s",
            self.get_middle_port(), self.get_instance_id())

        if self._wait_for_open_port(self.get_middle_checkup_port()):
            g_logger.debug("Started instance on middleport %d with ID %s has open port %d",
                self.get_middle_port(), self.get_instance_id(), self.get_middle_checkup_port())
            return True

        g_logger.debug("Started instance on middleport %d with ID %s has closed port %d",
            self.get_middle_port(), self.get_instance_id(), self.get_middle_checkup_port())
        self.stop()
        return False

    def stop(self):
        """ stop docker instance """
        middle_port = self.get_middle_port()
        cid = self.get_instance_id()
        g_logger.debug("Killing and removing %s (middleport %d)", cid, middle_port)

        try:
            self._instance.remove(force=True)
        except Exception as exc:
            g_logger.warning("Failed to remove instance for middleport %d, id %s: %s",
                middle_port, cid, exc)
            return False
        return True

    def _is_port_open(self, port, readtimeout=0.1):
        sock = socket.socket()
        ret = False
        g_logger.debug("Checking whether port %d is open...", port)

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

        g_logger.debug("result = %s", ret)
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

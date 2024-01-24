""" Check ports and allocate a new docker instance"""

import random
import socket
import time

from celery.utils.log import get_task_logger

from . import docker_instance

g_logger = get_task_logger(__name__)

class DockerPorts():
    ''' this is a global object that keeps track of the free ports
    when requested, it allocates a new docker instance and returns it '''

    IMAGELIMIT = 20

    def __init__(self):
        self.instances_by_name = {}
        self.image_params = {}
        self.inner_port = 22
        self.outer_port = 0

    def update_docker_options(self, docker_options):
        """ Add ports setup """

        self.outer_port = self.get_available_port()

        docker_options["detach"] = True

        if "ports" not in docker_options:
            docker_options["ports"] = {}
        docker_options["ports"][self.inner_port] = None
        docker_options["ports"][self.outer_port] = None

        return docker_options

    def create(self, message):
        """ create docker instance """

        image_name = message['docker_image_name']
        docker_options = message['docker_options']

        docker_options = self.update_docker_options(docker_options)

        icount = 0
        if image_name in self.instances_by_name:
            icount = len(self.instances_by_name[image_name])

        if icount >= self.IMAGELIMIT > 0:
            g_logger.warning(
                "Reached max count of %d (currently %d) for image %s",
                self.IMAGELIMIT, icount, image_name)
            return None

        instance = docker_instance.DockerInstance(
                image_name, docker_options, self.outer_port)
        instance.start()

        if image_name not in self.instances_by_name:
            self.instances_by_name[image_name] = []

        # in case of reuse, the list will have duplicates
        self.instances_by_name[image_name] += [instance]

        # Send the information of the recent created docker instance to rabbitmq
        #try:
        #    rabbit.send(instance.get_instance_info())
        #except pika.exceptions.AMQPConnectionError:
        #    g_logger.warning(
        #        "Cannot connect to rabbitmq. Are you sure it is running?")
        #else:
        #    g_logger.info(
        #        "Docker instance [%s] info sent to rabbitmq server",
        #        instance.get_instance_id())

        return instance

    def destroy(self, instance):
        """ destroy docker instance """

        image_name = instance.image_name

        # in case of reuse, the list will have duplicates, but remove() does not care
        self.instances_by_name[image_name].remove(instance)

        # stop the instance
        instance.stop()

    def _is_port_open(self, port, readtimeout=0.1):
        """ checks if port is open, so we can use it """

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

    def get_available_port(self):
        """ dynamic ports are from 49152-65535 """
        port = 49152

        while self._is_port_open(port):
            port = random.randrange(49152, 65535)

        g_logger.debug("Using port %d for the new container", port)

        return port

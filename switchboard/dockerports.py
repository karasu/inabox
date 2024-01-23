""" Check ports and allocate a new docker instance"""

from logger import g_logger

import dockerinstance

IMAGELIMIT = 20

class DockerPorts():
    ''' this is a global object that keeps track of the free ports
    when requested, it allocates a new docker instance and returns it '''

    CONFIG_PROFILEPREFIX = "profile:"
    CONFIG_DOCKEROPTIONSPREFIX = "dockeroptions:"

    def __init__(self):
        self.instances_by_name = {}
        self.image_params = {}

    def create(self, message):
        """ create docker instance """

        image_name = message['docker_image_name']
        docker_options = message['docker_options']

        icount = 0
        if image_name in self.instances_by_name:
            icount = len(self.instances_by_name[image_name])

        if icount >= IMAGELIMIT > 0:
            g_logger.warning(
                "Reached max count of %d (currently %d) for image %s",
                IMAGELIMIT, icount, image_name)
            return None

        instance = dockerinstance.DockerInstance(
                image_name, docker_options)
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

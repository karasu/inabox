""" Runs a container when asked """

import logging
import random
import sys

from logger import g_logger, CustomFormatter

import dockerports as dp
import rabbit

# Message is:
# { "docker_instance_id", "docker_options", "docker_image_name",
#  "port", "user_id", "challenge_id", "error_message"}


def setup_logger():
    """ Setup logger """

    # Log to a file
    handler = logging.FileHandler("switchboard.log")
    handler.setFormatter(CustomFormatter())
    g_logger.addHandler(handler)

    # Log to the screen, too
    handler = logging.StreamHandler()
    handler.setFormatter(CustomFormatter())
    g_logger.addHandler(handler)

    g_logger.setLevel(logging.DEBUG)

def request(message):
    """ Start a new docker instance """

    result = {
        "docker_options": message['docker_options'],
        "docker_image_name": message['docker_image_name'],
        "user_id": message['user_id'],
        "challenge_id": message['challenge_id'] }

    docker_instance = g_docker_ports.create(message)

    if docker_instance is None:
        g_logger.warning("Error creating a docker instance from %s", message)

        result['docker_instance_id'] = -1
        result['error'] = "Error creating container"
        result['port'] = 0
        return result

    # Instance created
    g_logger.info(
        "Incoming petition from user %s for a contanier from image %s",
        message["username"],
        docker_instance.get_instance_id())

    result['docker_instance_id'] = docker_instance.get_instance_id()
    result['port'] = docker_instance.get_port()
    result['error'] = None
    return result

def main():
    """ main function. Program starts here """

    random.seed()

    setup_logger()

    try:
        consumer = rabbit.Rabbit(request)
        consumer.run()
    except KeyboardInterrupt:
        consumer.close()
        sys.exit()

g_docker_ports = dp.DockerPorts()
g_docker_instances = {}

if __name__ == "__main__":
    main()

""" Runs a container when asked """

import logging
import random

from logger import g_logger, CustomFormatter

import dockerports as dp
import rabbit

# Message is:
# { "docker_instance_id", "user_id", "challenge_id", "docker_image_name",
# "message", "docker_options", "ssh_port"}

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


def main():
    """ main function. Program starts here """

    def request(message):
        """ Start a new docker instance """

        docker_instance = g_docker_ports.create(message)

        if docker_instance is None:
            g_logger.warning("Error creating a docker instance from %s", message)
            return {
                "docker_instance_id": -1,
                "user_id": message['user_id'],
                "challenge_id": message['challenge_id'],
                "docker_image_name": message['docker_image_name'],
                "message": f"Error creating container from image {message['docker_image_name']}"}

        # Instance created
        g_logger.info(
            "Incoming petition from user %s for a contanier from image %s",
            message["username"],
            docker_instance.get_instance_id())
        return {
            "docker_instance_id": docker_instance.get_instance_id(),
            "user_id": message['user_id'],
            "challenge_id": message['challenge_id'],
            "docker_image_name": message['docker_image_name']
        }

    random.seed()

    setup_logger()

    consumer = rabbit.Rabbit(request)
    consumer.run()

g_docker_ports = dp.DockerPorts()
g_docker_instances = {}

if __name__ == "__main__":
    main()

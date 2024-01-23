""" Runs a container when asked """

from logger import g_logger

import dockerports as dp
import rabbit

def main():
    """ main function. Program starts here """

    def request(params):
        """ Start a new docker instance """

        docker_instance = g_docker_ports.create(params['profilename'])

        if docker_instance is None:
            g_logger.warning("Error creating a docker instance from %s", params['profilename'])
            return {
                "docker_instance_id": -1,
                "user_id": params['user_id'],
                "challenge_id": params['challenge_id'],
                "message": f"Error creating a docker instance from {params['profilename']}"}
        else:
            g_logger.info(
                "Incoming petition from user %s for a contanier from image %s",
                params["username"],
                docker_instance.get_profile_name())
            return {
                "docker_instance_id": docker_instance.get_profile_name(),
                "user_id": params['user_id'],
                "challenge_id": params['challenge_id']
            }


    g_docker_ports.read_config('switchboard.conf')

    consumer = rabbit.Rabbit(request)
    consumer.run()

g_docker_ports = dp.DockerPorts()
g_docker_instances = {}

if __name__ == "__main__":
    main()

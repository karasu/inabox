""" Runs a container when asked """

import sys

from logger import g_logger

import rabbit


def main():
    """ main function. Program starts here """

    ports_and_names = g_docker_ports.read_config(
        sys.argv[1] if len(sys.argv) > 1 else 'switchboard.conf')

    try:
        for (name, outerport) in ports_and_names.items():
            g_logger.debug("Listening on port %d", outerport)
            reactor.listenTCP(
                outerport,
                DockerProxyFactory(name),
                interface=sys.argv[2] if len(sys.argv) > 2 else '')
        reactor.run()
    except twisted.internet.error.CannotListenError as err:
        print(err)

g_docker_ports = DockerPorts()

if __name__ == "__main__":
    main()

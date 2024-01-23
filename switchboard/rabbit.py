""" RPC server """

import json
import pika

from logger import g_logger

class Rabbit():
    """ Listens to inabox messages (using rabbitmq) """

    QUEUE = "switchboard"

    def __init__(self, request_func):
        self._connection = None
        self._channel = None
        self.request_func = request_func

    def on_request(self, channel, method, props, body):
        """ Create a docker container """    

        response = self.request_func(body)

        channel.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(
                correlation_id = props.correlation_id),
            body=json.dumps(response))

        channel.basic_ack(delivery_tag=method.delivery_tag)

    def close(self):
        """ closes the connection """
        if self._connection is not None:
            self._connection.close()

    def connect(self):
        """ Connect to rabbitmq """
        credentials = pika.PlainCredentials('guest', 'guest')

        parameters = pika.ConnectionParameters(
                host='localhost',
                port=5672,
                virtual_host='/',
                heartbeat=5,
                credentials=credentials
            )

        return pika.BlockingConnection(parameters)

    def setup_channel(self):
        """ Setups channel and queue """
        channel = self._connection.channel()

        # In order to spread the load equally over multiple servers we need
        # to set the prefetch_count setting
        channel.basic_qos(prefetch_count=1)

        channel.queue_declare(queue=self.QUEUE)

        channel.basic_consume(
            queue=self.QUEUE,
            auto_ack=True,
            on_message_callback=self.on_request)

        return channel

    def run(self):
        """ Setup connection and start consuming """

        try:
            g_logger.debug("Opening connection to rabbitmq...")
            self._connection = self.connect()

            g_logger.debug("Setting channel...")
            self._channel = self.setup_channel()

            g_logger.info(" [x] Awaiting RPC requests")
            self._channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as exc:
            g_logger.error("Error connecting to rabbitmq server: [%s]", exc)
            return

""" RPC server """
import json
import pika

from logger import g_logger

class Rabbit():
    """ Listens to inabox messages (using rabbitmq) """
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

    def connect(self):
        """ Connects to rabbitmq """
        self._connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))

        self._channel = self._connection.channel()

        self._channel.queue_declare(queue='switchboard')

    def run(self):
        """ Starts consuming """

        # In order to spread the load equally over multiple servers we need
        # to set the prefetch_count setting
        self._channel.basic_qos(prefetch_count=1)

        self._channel.basic_consume(
            queue='switchbox', on_message_callback=self.on_request)

        g_logger.info(" [x] Awaiting RPC requests")
        self._channel.start_consuming()

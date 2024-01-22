""" Celery. Create your tasks here """

import logging

import pika

from celery import shared_task
from celery.signals import worker_shutting_down

g_switchbox = None

class Switchbox():
    """ Listen to switchbox messages through rabbitmq (consumer) """

    QUEUE = 'switchbox'
    EXCHANGE = 'switchbox'
    EXCHANGE_TYPE = 'direct'

    def __init__(self):
        self._connection = None
        self._channel = None

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

        channel.exchange_declare(
            exchange=self.EXCHANGE,
            exchange_type=self.EXCHANGE_TYPE,
            passive=False,
            durable=True,
            auto_delete=False)

        channel.queue_declare(queue=self.QUEUE)

        channel.basic_consume(
            queue=self.QUEUE,
            auto_ack=True,
            on_message_callback=self.on_message)

        return channel

    def close(self):
        """ closes the connection """
        #print(sig, how, exitcode)
        if self._connection is not None:
            self._connection.close()

    def on_message(self, channel, method, properties, body):
        """ message callback """
        logging.debug("channel: %s", channel)
        logging.debug("method: %s", method)
        logging.debug("properties: %s", properties)
        logging.debug("body: %s", body)
        print(body)

    def run(self):
        """ Setup connection and start consuming """
        self._connection = self.connect()
        self._channel = self.setup_channel()
        self._channel.start_consuming()

@shared_task(bind=True)
def switchbox_task(task):
    """ Listen to switchbox messages """
    logging.debug("task: %s", task)
    try:
        g_switchbox = Switchbox()
        g_switchbox.run()
    except KeyboardInterrupt:
        g_switchbox.close()

@worker_shutting_down.connect
def shutting_down(**kwargs):
    """ Shutdown """
    if g_switchbox is not None:
        g_switchbox.close()
        print("CLOSING!")
    print("EOOOOO")

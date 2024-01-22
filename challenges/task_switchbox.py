""" Celery. Create your tasks here """

import pika

from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

class Switchbox():
    """ Listen to switchbox messages through rabbitmq (consumer) """

    QUEUE = "switchbox"

    def __init__(self, uid):
        self._connection = None
        self._channel = None
        self._uid = uid

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

    def on_message(self, channel, method, properties, body):
        """ message callback """
        logger.debug("channel: %s", channel)
        logger.debug("method: %s", method)
        logger.debug("properties: %s", properties)
        logger.info("body: %s", body)

    def setup_channel(self):
        """ Setups channel and queue """
        channel = self._connection.channel()

        channel.queue_declare(
            queue=self.QUEUE)

        channel.basic_consume(
            queue=self.QUEUE,
            auto_ack=True,
            on_message_callback=self.on_message)

        return channel

    def close(self):
        """ closes the connection """
        if self._connection is not None:
            self._connection.close()

    def run(self):
        """ Setup connection and start consuming """
        self._connection = self.connect()
        self._channel = self.setup_channel()
        self._channel.start_consuming()
        

@shared_task(bind=True)
def switchbox_task(self, user_id, challenge_id):
    """ Listen to switchbox messages """
    logger.debug("task: %s", self)

    uid = (user_id, challenge_id)
    switchbox = Switchbox(uid)
    return switchbox.run()

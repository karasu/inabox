""" Celery. Create your tasks here """

import time
from uuid import uuid4

from contextlib import contextmanager
import pika

from django.core.cache import cache

from celery import shared_task
from celery.utils.log import get_task_logger

LOCK_EXPIRE = 60 * 10  # Lock expires in 10 minutes

logger = get_task_logger(__name__)

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
        if self._connection is not None:
            self._connection.close()

    def on_message(self, channel, method, properties, body):
        """ message callback """
        logger.debug("channel: %s", channel)
        logger.debug("method: %s", method)
        logger.debug("properties: %s", properties)
        logger.debug("body: %s", body)

    def run(self):
        """ Setup connection and start consuming """
        self._connection = self.connect()
        self._channel = self.setup_channel()
        self._channel.start_consuming()

@contextmanager
def memcache_lock(lock_id, oid):
    timeout_at = time.monotonic() + LOCK_EXPIRE - 3
    # cache.add fails if the key already exists
    status = cache.add(lock_id, oid, LOCK_EXPIRE)
    try:
        yield status
    finally:
        # memcache delete is very slow, but we have to use it to take
        # advantage of using add() for atomic locking
        if time.monotonic() < timeout_at and status:
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else
            # also don't release the lock if we didn't acquire it
            cache.delete(lock_id)

@shared_task(bind=True)
def switchbox_task(self, oid):
    """ Listen to switchbox messages """
    #logger.debug("task: %s", task)
    
    switchbox = Switchbox()
    lock_id = "this-is-a-test"
    with memcache_lock(lock_id, self.app.oid) as acquired:
        if acquired:
            logger.debug("Running switchbox listening task")
            switchbox.run()
    logger.debug("Switchbox task already running")


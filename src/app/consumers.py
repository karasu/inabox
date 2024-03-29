""" Channels consumers """

import json
import struct
import weakref
import asyncio
import paramiko

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

try:
    from types import UnicodeType
except ImportError:
    UnicodeType = str

#from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer

#from .worker import Worker, recycle_worker
from .worker import clients
from .privatekey import InvalidValueError

from .logger import g_logger

# WsockHandler
class SshConsumer(AsyncWebsocketConsumer):
    """ Consumer ssh websocket """
    worker_ref = None
    groups = ["all_terminals"]

    def __init__(self):
        super().__init__()

        self.src_addr = None
        self._weakref = None

    async def connect(self):
        self.src_addr = self.scope['client']
        src_ip = self.src_addr[0]

        g_logger.debug('Connected from %s', src_ip)

        workers = clients.get(src_ip, None)

        if not workers:
            g_logger.debug("Worker not found")
            g_logger.warning('Websocket authentication failed.')
            await self.close()
            return

        try:
            query = self.scope['query_string'].decode("utf-8")
            for pair in query.split(','):
                if pair.startswith('workerid='):
                    worker_id = pair.split('=')[1]
        except (KeyError, InvalidValueError):
            await self.close()
        else:
            # g_logger.debug("worker_id)

            worker = workers.get(worker_id)
            if worker:
                # Remove worker from workers list
                workers[worker_id] = None
                #self.set_nodelay(True)
                # set us as handler
                worker.set_handler(self)

                # store consumer reference
                self._weakref = weakref.ref(self)

                # store worker reference
                self.worker_ref = weakref.ref(worker)

                loop = asyncio.get_event_loop()

                loop.add_reader(
                    worker.file_desc, worker.read, self._weakref)
                loop.add_writer(
                    worker.file_desc, worker.write, self._weakref)

                await self.accept()
            else:
                g_logger.debug("Worker not found")
                g_logger.warning('Websocket authentication failed.')
                await self.close()

    async def disconnect(self, code):
        # Called when the socket closes
        g_logger.warning("Connection closed.")

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        g_logger.debug('%s from %s:%d', text_data, self.src_addr[0], self.src_addr[1])

        worker = self.worker_ref()
        if not worker:
            # The worker has likely been closed. Do not process.
            g_logger.debug(
                "Received message to closed worker from %s:%d",
                self.src_addr[0], self.src_addr[1])
            g_logger.debug('No worker found')
            self.close()
            return

        if worker.closed:
            g_logger.debug('Worker closed')
            self.close()
            return

        try:
            msg = json.loads(text_data)
        except JSONDecodeError:
            return

        if not isinstance(msg, dict):
            return

        resize = msg.get('resize')
        if resize and len(resize) == 2:
            try:
                worker.chan.resize_pty(*resize)
            except (TypeError, struct.error, paramiko.SSHException) as err:
                g_logger.debug(err)

        data = msg.get('data')
        if data and isinstance(data, UnicodeType):
            worker.data_to_dst.append(data)
            worker.write(self._weakref)

    async def send_message(self, event):
        """ Send data to terminal """
        if event["data"]:
            await self.send(bytes_data=event["data"])

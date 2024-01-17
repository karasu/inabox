""" Channels consumers """

import json
import logging
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
        logging.debug('Connected from {}:{}'.format(*self.src_addr))

        src_ip = self.src_addr[0]
        workers = clients.get(src_ip, None)

        if not workers:
            logging.debug("Worker not found 1")
            logging.warning('Websocket authentication failed.')
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
            # logging.debug("worker_id)

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
                    worker.fd, worker.read, self._weakref)
                loop.add_writer(
                    worker.fd, worker.write, self._weakref)

                await self.accept()
            else:
                logging.debug("Worker not found 2")
                logging.warning('Websocket authentication failed.')
                await self.close()

    async def disconnect(self, code):
        # Called when the socket closes
        print("SOCKET CLOSED!")

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        logging.debug('{!r} from {}:{}'.format(text_data, *self.src_addr))

        print('{!r} from {}:{}'.format(text_data, *self.src_addr))

        worker = self.worker_ref()
        if not worker:
            # The worker has likely been closed. Do not process.
            logging.debug(
                "received message to closed worker from {}:{}".format(*self.src_addr))
            logging.debug('No worker found')
            self.close()
            return

        if worker.closed:
            logging.debug('Worker closed')
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
                logging.debug(err)

        data = msg.get('data')
        if data and isinstance(data, UnicodeType):
            worker.data_to_dst.append(data)
            worker.write(self._weakref)

    async def send_message(self, event):
        """ Send data to terminal """
        if event["data"]:
            await self.send(bytes_data=event["data"])

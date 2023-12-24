import json
import logging
import os
import struct
import weakref
import socket
import threading
import asyncio

try:
    from types import UnicodeType
except ImportError:
    UnicodeType = str

from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer

from .worker import Worker, recycle_worker, clients
from .args import InvalidValueError

# These constants were originally based on constants from the
# epoll module.
IOLoop_NONE = 0
IOLoop_READ = 0x001
IOLoop_WRITE = 0x004
IOLoop_ERROR = 0x018


# WsockHandler
class SshConsumer(AsyncWebsocketConsumer):
    worker_ref = None
    groups = ["broadcast"]

    async def connect(self):
        self.src_addr = self.scope['client']
        logging.info('Connected from {}:{}'.format(*self.src_addr))

        print('Connected from {}:{}'.format(*self.src_addr))
        
        src_ip = self.src_addr[0]
        workers = clients.get(src_ip, None)

        if not workers:
            print("Worker not found 1")
            logging.warning('Websocket authentication failed.')
            await self.close()
            return



        try:
            query = self.scope['query_string'].decode("utf-8")
            for pair in query.split(','):
                if pair.startswith('workerid='):
                    worker_id = pair.split('=')[1]
        except (KeyError, InvalidValueError) as err:
            self.close(reason=str(err))
        else:
            print("worker_id:", worker_id)

            worker = workers.get(worker_id)
            if worker:
                workers[worker_id] = None
                #self.set_nodelay(True)
                worker.set_handler(self)
                self.worker_ref = weakref.ref(worker)


                loop = asyncio.get_event_loop()
                # TODO: Fix this
                #self.loop.add_handler(worker.fd, worker, IOLoop.READ)
                #self.loop.add_signal_handler(worker.fd, worker, IOLoop.READ)
                
                
                #if threading.current_thread() is threading.main_thread():
                #    worker.loop.add_signal_handler(worker.fd, worker, IOLoop_READ)

                await self.accept()
            else:
                print("Worker not found 2")
                logging.warning('Websocket authentication failed.')
                await self.close()


    #async def disconnect(self, close_code):
    #    # Called when the socket closes
    #    pass

    # Receive message from WebSocket
    async def receive(self, text_data):
       
        
        logging.debug('{!r} from {}:{}'.format(text_data, *self.src_addr))
        worker = self.worker_ref()
        if not worker:
            # The worker has likely been closed. Do not process.
            logging.debug(
                "received message to closed worker from {}:{}".format(
                    *self.src_addr
                )
            )
            logging.debug('No worker found')
            print('No worker found 3')
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
        
        print(msg)

        resize = msg.get('resize')
        if resize and len(resize) == 2:
            try:
                worker.chan.resize_pty(*resize)
            except (TypeError, struct.error, paramiko.SSHException) as err:
                logging.debug(err)

        data = msg.get('data')
        if data and isinstance(data, UnicodeType):
            print("worker.on_write()")
            worker.data_to_dst.append(data)
            worker.on_write()
        

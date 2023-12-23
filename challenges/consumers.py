import json
import logging
import os
import struct
import weakref
import socket
import threading

try:
    from types import UnicodeType
except ImportError:
    UnicodeType = str

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from .worker import Worker, recycle_worker, clients
from .args import InvalidValueError

# These constants were originally based on constants from the
# epoll module.
IOLoop_NONE = 0
IOLoop_READ = 0x001
IOLoop_WRITE = 0x004
IOLoop_ERROR = 0x018

'''
from channels.generic.websocket import AsyncWebsocketConsumer

class MyConsumer(AsyncWebsocketConsumer):
    groups = ["broadcast"]
    loop = asyncio.get_event_loop()

    async def connect(self):
        # Called on connection.
        # To accept the connection call:
        await self.accept()
        # Or accept the connection and specify a chosen subprotocol.
        # A list of subprotocols specified by the connecting client
        # will be available in self.scope['subprotocols']
        await self.accept("subprotocol")
        # To reject the connection, call:
        await self.close()

    async def receive(self, text_data=None, bytes_data=None):
        # Called with either text_data or bytes_data for each frame
        # You can call:
        await self.send(text_data="Hello world!")
        # Or, to send a binary frame:
        await self.send(bytes_data="Hello world!")
        # Want to force-close the connection? Call:
        await self.close()
        # Or add a custom WebSocket error code!
        await self.close(code=4123)

    async def disconnect(self, close_code):
        # Called when the socket closes

await create_evenloop()
'''


# WsockHandler
class SshConsumer(WebsocketConsumer):
    worker_ref = None

    def connect(self):        
        self.group_name = "challenge_id_" + self.scope['url_route']['kwargs']['challenge_id']
        print("Group name:" + self.group_name)
        # Join room group
        async_to_sync(self.channel_layer.group_add) (
            self.group_name, self.channel_name
        )

        

        #self.send(text_data=json.dumps(self.result))

        self.src_addr = self.scope['client']
        logging.info('Connected from {}:{}'.format(*self.src_addr))

        workers = clients.get(self.scope['client'][0])
        if not workers:
            logging.warning('Websocket authentication failed.')
            self.close()
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
                #self.loop.add_handler(worker.fd, worker, IOLoop.READ)
                #self.loop.add_signal_handler(worker.fd, worker, IOLoop.READ)
                
                
                #if threading.current_thread() is threading.main_thread():
                #    worker.loop.add_signal_handler(worker.fd, worker, IOLoop_READ)

                self.accept()
            else:
                logging.warning('Websocket authentication failed.')
                self.close()

        
        


    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )
        print("disconnect")

    # Receive message from WebSocket
    def receive(self, text_data):
       
        
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
            print('No worker found')
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
        





        # Send message to room group
        #async_to_sync(self.channel_layer.group_send)(
        #    self.group_name, {"type": "ssh_message", "message": message}
        #)

    # Receive message from room group
    def ssh_message(self, event):
        message = event["message"]
        print("message from room group")
        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message}))

    
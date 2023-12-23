import json
import logging
import os
import struct
import weakref
import socket

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from .worker import Worker, recycle_worker, clients
from .args import InvalidValueError

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
        try:
            message = json.loads(text_data)
        except JSONDecodeError:
            return
        
        if not isinstance(message, dict):
            return
        
        print(message)
        
        logging.debug('{!r} from {}:{}'.format(message, *self.src_addr))
        worker = self.worker_ref()
        if not worker:
            # The worker has likely been closed. Do not process.
            logging.debug(
                "received message to closed worker from {}:{}".format(
                    *self.src_addr
                )
            )
            print('No worker found')
            self.close()
            return

        '''
        logging.debug('{!r} from {}:{}'.format(message, *self.src_addr))
        worker = self.worker_ref()
        if not worker:
            # The worker has likely been closed. Do not process.
            logging.debug(
                "received message to closed worker from {}:{}".format(
                    *self.src_addr
                )
            )
            self.close(reason='No worker found')
            return

        if worker.closed:
            self.close(reason='Worker closed')
            return

        try:
            msg = json.loads(message)
        except JSONDecodeError:
            return

        if not isinstance(msg, dict):
            return

        resize = msg.get('resize')
        if resize and len(resize) == 2:
            try:
                worker.chan.resize_pty(*resize)
            except (TypeError, struct.error, paramiko.SSHException):
                pass

        data = msg.get('data')
        if data and isinstance(data, UnicodeType):
            worker.data_to_dst.append(data)
            worker.on_write()
        '''





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

    
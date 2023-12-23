import json
import logging
import os
import struct

import socket

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from .worker import Worker, recycle_worker, clients

# WsockHandler
class SshConsumer(WebsocketConsumer):
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
            self.close(reason='Websocket authentication failed.')
            return



        try:
            worker_id = self.get_value('id')
            
        except (tornado.web.MissingArgumentError, InvalidValueError) as exc:
            self.close(reason=str(exc))
        else:
            worker = workers.get(worker_id)
            if worker:
                workers[worker_id] = None
                self.set_nodelay(True)
                worker.set_handler(self)
                self.worker_ref = weakref.ref(worker)
                self.loop.add_handler(worker.fd, worker, IOLoop.READ)
                self.accept()
            else:
                self.close(reason='Websocket authentication failed.')

        


    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )
        print("disconnect")

    # Receive message from WebSocket
    def receive(self, text_data):
        try:
            msg = json.loads(text_data)
        except JSONDecodeError:
            return
        
        if not isinstance(msg, dict):
            return
        
        print(msg)
        
      
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

    
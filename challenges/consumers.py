import json
import logging
import os
import struct

import socket

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# WsockHandler
class SshConsumer(WebsocketConsumer):
    def connect(self):        
        self.group_name = "challenge_id_" + self.scope['url_route']['kwargs']['challenge_id']
        print("Group name:" + self.group_name)
        # Join room group
        async_to_sync(self.channel_layer.group_add) (
            self.group_name, self.channel_name
        )


        print("Connect")

        self.accept()
        self.send(text_data=json.dumps(self.result))





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

    
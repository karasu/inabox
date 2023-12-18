import json
import logging

import socket
import paramiko
from .sshclient import SSHClient

'''
from channels.generic.websocket import AsyncWebsocketConsumer


https://www.honeybadger.io/blog/django-channels-websockets-chat/

class ChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_box_name = self.scope["url_route"]["kwargs"]["chat_box_name"]
        self.group_name = "chat_%s" % self.chat_box_name

        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
    # This function receive messages from WebSocket.
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        username = text_data_json["username"]

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chatbox_message",
                "message": message,
                "username": username,
            },
        )
    # Receive message from room group.
    async def chatbox_message(self, event):
        message = event["message"]
        username = event["username"]
        #send message and username of sender to websocket
        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "username": username,
                }
            )
        )

    pass
'''

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

class SshConsumer(WebsocketConsumer):
    def connect(self):        
        self.group_name = "challenge_id_" + self.scope['url_route']['kwargs']['challenge_id']
                
        # Join room group
        async_to_sync(self.channel_layer.group_add) (
            self.group_name, self.channel_name
        )


        self.accept()

        self.result = dict(id=None, status=None, encoding=None)

        self.ssh_client = SSHClient()

        args = ('localhost', 22, 'test', 'test', None)
        try:
            self.ssh_connect(args)
            status = "ok"
        except ValueError as err:
            status = str(err)
        except paramiko.SSHException as err:
            status = str(err)

        self.result.update(status=status)
        self.result.update(id=1, encoding='ascii')
        self.send(text_data=json.dumps(status))


    def ssh_connect(self, args):
        ssh = self.ssh_client
        try:
            ssh.connect(*args, timeout=1)
        except socket.error:
            raise ValueError('Unable to connect.')
        except paramiko.BadAuthenticationType:
            raise ValueError('Bad authentication type.')
        except paramiko.AuthenticationException:
            raise ValueError('Authentication failed.')
        except paramiko.BadHostKeyException:
            raise ValueError('Bad host key.')

        term = self.get_argument('term', u'') or u'xterm'
        self.chan = ssh.invoke_shell(term=term)
        self.chan.setblocking(0)

    '''
    def get_ssh_client(self):
        ssh = SSHClient()
        ssh._system_host_keys = self.host_keys_settings['system_host_keys']
        ssh._host_keys = self.host_keys_settings['host_keys']
        ssh._host_keys_filename = self.host_keys_settings['host_keys_filename']
        ssh.set_missing_host_key_policy(self.policy)
        return ssh
    '''
    '''
    def ssh_connect(self, args):
        ssh = self.ssh_client
        dst_addr = args[:2]
        logging.info('Connecting to {}:{}'.format(*dst_addr))

        try:
            ssh.connect(*args, timeout=options.timeout)
        except socket.error:
            raise ValueError('Unable to connect to {}:{}'.format(*dst_addr))
        except paramiko.BadAuthenticationType:
            raise ValueError('Bad authentication type.')
        except paramiko.AuthenticationException:
            raise ValueError('Authentication failed.')
        except paramiko.BadHostKeyException:
            raise ValueError('Bad host key.')

        term = self.get_argument('term', u'') or u'xterm'
        chan = ssh.invoke_shell(term=term)
        chan.setblocking(0)
        worker = Worker(self.loop, ssh, chan, dst_addr)
        worker.encoding = options.encoding if options.encoding else \
            self.get_default_encoding(ssh)
        return worker

    '''


    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        #message = text_data_json["data"]

        print(text_data_json)
        # Send message to room group
        #async_to_sync(self.channel_layer.group_send)(
        #    self.group_name, {"type": "ssh_message", "message": message}
        #)

    # Receive message from room group
    def ssh_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message}))

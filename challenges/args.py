""" Store ssh configuration here """

import base64
import logging

from django.core.exceptions import PermissionDenied

from .privatekey import InvalidValueError, PrivateKey

from .utils import (
    is_valid_ip_address, is_valid_port, is_valid_hostname, to_int
)


DEFAULT_PORT=22

class Args():
    """ Get ssh arguments """

    def __init__(self, request, host_keys, system_host_keys):
        self.request = request
        self.post = request.POST
        self._host_keys = host_keys
        self._system_host_keys = system_host_keys

    def get_privatekey(self):
        """ get private key from request """
        return None, None
        # name = 'privatekey'
        # lst = self.request.files.get(name)
        # if lst:
        #     # multipart form
        #     filename = lst[0]['filename']
        #     data = lst[0]['body']
        #     value = self.decode_argument(data, name=name).strip()
        # else:
        #     # urlencoded form
        #     value = self.get_argument(name, '')
        #     filename = ''
        # return value, filename

    def get_hostname(self):
        """ return hostname """
        value = self.get_value('hostname')
        if not (is_valid_hostname(value) or is_valid_ip_address(value)):
            raise InvalidValueError(f'Invalid hostname: {value}')
        return value

    def get_port(self):
        """ return connection port """
        value = self.post.get('port', '')
        if not value:
            return DEFAULT_PORT

        port = to_int(value)
        if port is None or not is_valid_port(port):
            raise InvalidValueError(f'Invalid port: {value}')
        return port

    def lookup_hostname(self, hostname, port):
        """ Try to find hostname in host keys """

        if port == 22:
            key = hostname
        else:
            key = f"[{hostname}]:{port}"

        if self._host_keys.lookup(key) is None:
            if self._system_host_keys.lookup(key) is None:
                raise PermissionDenied()


    def get_value(self, name):
        """ Get value from GET """
        value = self.post.get(name)
        if not value:
            raise InvalidValueError(f'Missing value {name}')
        return value

    def get_client_ip_and_port(self):
        """ Get ip and port from header """
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # running behind a proxy
            ip_address = x_forwarded_for.split(',')[0]
            port = self.request.META.get('HTTP_X_FORWARDED_PORT')
        else:
            ip_address = self.request.META.get('REMOTE_ADDR')
            port = self.request.META.get('REMOTE_PORT')
        return (ip_address, port)

    def decode64str(self, string):
        """ decode b64 encoded string """
        # Encode the str into bytes.
        bencoded = string.encode("utf-8")
        # decode b64
        bdecoded = base64.b64decode(bencoded)
        # return decoded string
        return bdecoded.decode("utf-8")

    def get_args(self):
        """ Get all ssh parameters """
        hostname = self.get_hostname()
        port = self.get_port()
        username = self.get_value('username')
        password = self.decode64str(self.post.get('password', ''))

        if password != "inabox":
            raise ValueError(password)

        privatekey, filename = self.get_privatekey()
        passphrase = self.post.get('passphrase', '')

        totp = self.post.get('totp', '')

        #if isinstance(self.policy, paramiko.RejectPolicy):
        #    self.lookup_hostname(hostname, port)

        if privatekey:
            pkey = PrivateKey(privatekey, passphrase, filename).get_pkey_obj()
        else:
            pkey = None

        # self.ssh_client.totp = totp
        args = (hostname, port, username, password, pkey)
        logging.debug(args)

        return args

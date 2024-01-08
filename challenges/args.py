from .privatekey import PrivateKey

import base64
import logging


class InvalidValueError(Exception):
    pass

from .utils import (
    is_valid_ip_address, is_valid_port, is_valid_hostname
)

class Args():

    def __init__(self, request):
        self.request = request
        self.post = request.POST

    def get_privatekey(self):
        # TODO
        return None, None
        '''
        name = 'privatekey'
        lst = self.request.files.get(name)
        if lst:
            # multipart form
            filename = lst[0]['filename']
            data = lst[0]['body']
            value = self.decode_argument(data, name=name).strip()
        else:
            # urlencoded form
            value = self.get_argument(name, u'')
            filename = ''

        return value, filename
        '''

    def get_hostname(self):
        value = self.get_value('hostname')
        if not (is_valid_hostname(value) or is_valid_ip_address(value)):
            raise InvalidValueError('Invalid hostname: {}'.format(value))
        return value

    def get_port(self):
        value = self.post.get('port', u'')
        if not value:
            return DEFAULT_PORT

        port = to_int(value)
        if port is None or not is_valid_port(port):
            raise InvalidValueError('Invalid port: {}'.format(value))
        return port

    def lookup_hostname(self, hostname, port):
        key = hostname if port == 22 else '[{}]:{}'.format(hostname, port)

        if self.ssh_client._system_host_keys.lookup(key) is None:
            if self.ssh_client._host_keys.lookup(key) is None:
                raise tornado.web.HTTPError(
                        403, 'Connection to {}:{} is not allowed.'.format(
                            hostname, port)
                    )

    def get_value(self, name):
        value = self.post.get(name)
        if not value:
            raise InvalidValueError('Missing value {}'.format(name))
        return value

    def get_client_ip_and_port(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # running behind a proxy
            ip = x_forwarded_for.split(',')[0]
            port = self.request.META.get('HTTP_X_FORWARDED_PORT')
        else:
            ip = self.request.META.get('REMOTE_ADDR')
            port = self.request.META.get('REMOTE_PORT')
        return (ip, port)

    def decode64str(self, s):
        # Encode the str into bytes.
        bencoded = s.encode("utf-8")
        # decode b64
        bdecoded = base64.b64decode(bencoded)
        # return decoded string
        return bdecoded.decode("utf-8")

    def get_args(self):
        hostname = self.get_hostname()
        port = self.get_port()
        username = self.get_value('username')
        password = self.decode64str(self.post.get('password', u''))

        if password != "inabox":
            raise ValueError(password)

        privatekey, filename = self.get_privatekey()
        passphrase = self.post.get('passphrase', u'')

        totp = self.post.get('totp', u'')

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

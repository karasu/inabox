""" Manage private key for ssh connection """

import io
import logging

import paramiko

from .utils import to_bytes

from .logger import g_logger

class InvalidValueError(Exception):
    """ Exception class used in ssh code """


class PrivateKey():
    """ Store ssh private key """
    max_length = 16384  # rough number

    tag_to_name = {
        'RSA': 'RSA',
        'DSA': 'DSS',
        'EC': 'ECDSA',
        'OPENSSH': 'Ed25519'
    }

    def __init__(self, privatekey, password=None, filename=''):
        self.privatekey = privatekey
        self.filename = filename
        self.password = password
        self.check_length()
        self.iostr = io.StringIO(privatekey)
        self.last_exception = None

    def check_length(self):
        """ checks key length """
        if len(self.privatekey) > self.max_length:
            raise InvalidValueError('Invalid key length.')

    def parse_name(self, iostr, tag_to_name):
        """ gets key name """
        name = None
        length = 0
        for line_ in iostr:
            line = line_.strip()
            if line and line.startswith('-----BEGIN ') and \
                    line.endswith(' PRIVATE KEY-----'):
                lst = line.split(' ')
                if len(lst) == 4:
                    tag = lst[1]
                    if tag:
                        name = tag_to_name.get(tag)
                        if name:
                            length = len(line_)
                            break
        return name, length

    def get_specific_pkey(self, name, offset, password):
        """ gets specific private key """
        self.iostr.seek(offset)
        g_logger.debug("Reset offset to %d", offset)

        g_logger.debug("Try parsing it as %s type key", name)
        pkeycls = getattr(paramiko, name+'Key')
        pkey = None

        try:
            pkey = pkeycls.from_private_key(self.iostr, password=password)
        except paramiko.PasswordRequiredException as exc:
            raise InvalidValueError('Need a passphrase to decrypt the key.') from exc
        except (paramiko.SSHException, ValueError) as exc:
            self.last_exception = exc
            g_logger.debug(str(exc))

        return pkey

    def get_pkey_obj(self):
        """ Gets private key object """
        g_logger.info("Parsing private key %s", self.filename)
        name, length = self.parse_name(self.iostr, self.tag_to_name)
        if not name:
            raise InvalidValueError(f"Invalid key {self.filename}.")

        offset = self.iostr.tell() - length
        password = to_bytes(self.password) if self.password else None
        pkey = self.get_specific_pkey(name, offset, password)

        if pkey is None and name == 'Ed25519':
            for name in ['RSA', 'ECDSA', 'DSS']:
                pkey = self.get_specific_pkey(name, offset, password)
                if pkey:
                    break

        if pkey:
            return pkey

        g_logger.error(str(self.last_exception))

        msg = 'Invalid key'

        if self.password:
            msg = f"Invalid key or wrong passphrase '{self.password}' for decrypting it."

        raise InvalidValueError(msg)

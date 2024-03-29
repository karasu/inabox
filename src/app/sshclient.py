""" SSH Client module """

import paramiko

from .logger import g_logger

class SSHClient(paramiko.SSHClient):
    """ Paramiko SSH Client class """

    def __init__(self, host_keys_settings):
        """ initialize class """
        super().__init__()
        self.totp = None
        self.password = ""
        self._system_host_keys = host_keys_settings['system_host_keys']
        self._host_keys = host_keys_settings['host_keys']
        self._host_keys_filename = host_keys_settings['host_keys_filename']

    def get_host_keys(self):
        """ returns stored host keys """
        return self._host_keys

    def get_system_host_keys(self):
        """ returns stored system host keys """
        return self._system_host_keys

    def handler(self, _title, _instructions, prompt_list):
        """ handles connection """
        answers = []
        for prompt_, _ in prompt_list:
            prompt = prompt_.strip().lower()
            if prompt.startswith('password'):
                answers.append(self.password)
            elif prompt.startswith('verification'):
                answers.append(self.totp)
            else:
                raise ValueError(f"Unknown prompt: {prompt_}")
        return answers

    def auth_interactive(self, username, handler):
        """ verifies that totp has the verification code """
        if not self.totp:
            raise ValueError('Need a verification code for 2fa.')
        self._transport.auth_interactive(username, handler)

    def _auth(self, username, password, pkey, *_args):
        self.password = password
        saved_exception = None
        two_factor = False
        allowed_types = set()
        two_factor_types = {'keyboard-interactive', 'password'}

        if pkey is not None:
            g_logger.info('Trying publickey authentication')
            try:
                allowed_types = set(
                    self._transport.auth_publickey(username, pkey)
                )
                two_factor = allowed_types & two_factor_types
                if not two_factor:
                    return None
            except paramiko.SSHException as exc:
                saved_exception = exc

        if two_factor:
            g_logger.info('Trying publickey 2fa')
            return self.auth_interactive(username, self.handler)

        if password is not None:
            g_logger.info('Trying password authentication')
            try:
                self._transport.auth_password(username, password)
                return None
            except paramiko.SSHException as exc:
                saved_exception = exc
                allowed_types = set(getattr(exc, 'allowed_types', []))
                two_factor = allowed_types & two_factor_types

        if two_factor:
            g_logger.info('Trying password 2fa')
            return self.auth_interactive(username, self.handler)

        assert saved_exception is not None
        raise saved_exception

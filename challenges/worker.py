""" ssh connection worker """

import logging
import asyncio
try:
    import secrets
except ImportError:
    secrets = None

from uuid import uuid4

from channels.layers import get_channel_layer
channel_layer = get_channel_layer()

# These constants were originally based on constants from the
# epoll module.
IOLOOP_NONE = 0
IOLOOP_READ = 0x001
IOLOOP_WRITE = 0x004
IOLOOP_ERROR = 0x018

BUF_SIZE = 32 * 1024
clients = {}  # {ip: {id: worker}}


def clear_worker(worker, clients):
    """ removes worker """
    ip = worker.src_addr[0]
    workers = clients.get(ip)
    assert worker.id in workers
    workers.pop(worker.id)

    if not workers:
        clients.pop(ip)
        if not clients:
            clients.clear()


def recycle_worker(worker):
    """ reuses a worker """
    if worker.handler:
        return
    logging.warning('Recycling worker {}'.format(worker.id))
    worker.close(reason='worker recycled')


class Worker(object):
    """ Worker for ssh connections """
    def __init__(self, loop, ssh, chan, dst_addr):
        self.loop = loop
        self.ssh = ssh
        self.chan = chan
        self.src_addr = None
        self.dst_addr = dst_addr
        self.fd = chan.fileno()
        self.id = self.gen_id()
        self.data_to_dst = []
        self.handler = None
        self.mode = IOLOOP_READ
        self.closed = False

    @classmethod
    def gen_id(cls):
        """ creates a uid """
        return secrets.token_urlsafe(nbytes=32) if secrets else uuid4().hex

    def set_handler(self, handler):
        """ sets handler """
        if not self.handler:
            self.handler = handler

    def update_handler(self, mode):
        """ updates handler """
        if self.mode != mode:
            self.loop.update_handler(self.fd, mode)
            self.mode = mode
        if mode == IOLOOP_WRITE:
            self.loop.call_later(0.1, self, self.fd, IOLOOP_WRITE)

    def remove_handler(self):
        """ remove handler """
        if self.loop:
            self.loop.remove_reader(self.fd)
            self.loop.remove_writer(self.fd)

    def read(self, consumer):
        """ read data and send it to the consumer """
        logging.debug('worker {} on read'.format(self.id))
        try:
            data = self.chan.recv(BUF_SIZE)
        except (OSError, IOError) as err:
            logging.error(err)
            if self.chan.closed or errno_from_exception(err) in _ERRNO_CONNRESET:
                self.close(reason='chan error on reading')
        else:
            logging.debug('{!r} from {}:{}'.format(data, *self.dst_addr))
            if not data:
                self.close(reason='chan closed')
                return

            logging.debug('{!r} to {}:{}'.format(data, *self.handler.src_addr))
            try:
                # send a bytes frame to the consumer
                loop = asyncio.get_event_loop()
                channel_name = consumer().channel_name
                loop.create_task(channel_layer.send(channel_name, {
                    "type": "send.message", 
                    "data": data}))
            except:
                self.close(reason='websocket closed')

    def write(self, consumer):
        """ write data """
        logging.debug('worker {} on write'.format(self.id))

        if not self.data_to_dst:
            return

        data = ''.join(self.data_to_dst)
        logging.debug('{!r} to {}:{}'.format(data, *self.dst_addr))

        try:
            sent = self.chan.send(data)
        except (OSError, IOError) as e:
            logging.error(e)
            if self.chan.closed or errno_from_exception(e) in _ERRNO_CONNRESET:
                self.close(reason='chan error on writing')
            else:
                self.update_handler(IOLOOP_WRITE)
        else:
            self.data_to_dst = []
            data = data[sent:]
            if data:
                self.data_to_dst.append(data)
                self.update_handler(IOLOOP_WRITE)
            else:
                self.update_handler(IOLOOP_READ)

    def close(self, reason=None):
        """ close worker """
        if self.closed:
            return
        self.closed = True

        logging.info(
            'Closing worker {} with reason: {}'.format(self.id, reason))

        if self.handler:
            # TODO: Fix this! remove_handler
            # self.loop.remove_handler(self.fd)
            self.handler.close()
        self.chan.close()
        self.ssh.close()
        logging.info(
            'Connection to {}:{} lost'.format(*self.dst_addr))

        clear_worker(self, clients)
        logging.debug(clients)

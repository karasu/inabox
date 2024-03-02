""" ssh connection worker """

import asyncio
import errno

try:
    import secrets
except ImportError:
    secrets = None

from uuid import uuid4

from channels.layers import get_channel_layer
from .logger import g_logger

g_channel_layer = get_channel_layer()

# These constants were originally based on constants from the
# epoll module.
IOLOOP_NONE = 0
IOLOOP_READ = 0x001
IOLOOP_WRITE = 0x004
IOLOOP_ERROR = 0x018

BUF_SIZE = 32 * 1024

clients = {}  # {ip: {id: worker}}


def clear_worker(worker):
    """ removes worker """
    ip_address = worker.src_addr[0]
    workers = clients.get(ip_address)
    assert worker.gid in workers
    workers.pop(worker.gid)

    if not workers:
        clients.pop(ip_address)
        if not clients:
            clients.clear()


def recycle_worker(worker):
    """ reuses a worker """
    if worker.handler:
        return
    g_logger.warning("Recycling worker %s", worker.gid)
    worker.close(reason='worker recycled')


class Worker():
    """ Worker for ssh connections """
    def __init__(self, loop, ssh, chan, dst_addr):
        self.loop = loop
        self.ssh = ssh
        self.chan = chan
        self.src_addr = None
        self.dst_addr = dst_addr
        self.file_desc = chan.fileno()
        self.gid = self.gen_id()
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
            self.loop.update_handler(self.file_desc, mode)
            self.mode = mode
        if mode == IOLOOP_WRITE:
            self.loop.call_later(0.1, self, self.file_desc, IOLOOP_WRITE)

    def remove_handler(self):
        """ remove handler """
        if self.loop:
            self.loop.remove_reader(self.file_desc)
            self.loop.remove_writer(self.file_desc)

    def read(self, consumer):
        """ read data and send it to the consumer """
        g_logger.debug("worker %s on read", self.gid)
        try:
            data = self.chan.recv(BUF_SIZE)
        except (OSError, IOError) as exc:
            g_logger.error(exc)
            if self.chan.closed or exc.errno == errno.ECONNRESET:
                self.close(reason='chan error on reading')
        else:
            # g_logger.debug("%s from %s:%d", data, self.dst_addr[0], self.dst_addr[1])
            if not data:
                self.close(reason='chan closed')
                return

            #g_logger.debug("%s to %s:%d",
            #               data, self.handler.src_addr[0], self.handler.src_addr[1])
            try:
                # send a bytes frame to the consumer
                loop = asyncio.get_event_loop()
                channel_name = consumer().channel_name
                loop.create_task(g_channel_layer.send(
                    channel_name,
                    {"type": "send.message", "data": data}))
            except Exception:
                self.close(reason='websocket closed')

    def write(self, _consumer):
        """ write data """
        g_logger.debug("worker %s on write", self.gid)

        if not self.data_to_dst:
            return

        data = ''.join(self.data_to_dst)
        g_logger.debug("%s to %s:%d", data, self.dst_addr[0], self.dst_addr[1])

        try:
            sent = self.chan.send(data)
        except (OSError, IOError) as exc:
            g_logger.error(exc)
            if self.chan.closed or exc.errno == errno.ECONNRESET:
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

        g_logger.info(
            "Closing worker %s with reason: %s", self.gid, reason)

        if self.handler:
            # TODO: Fix this! remove_handler
            # self.loop.remove_handler(self.file_desc)
            self.handler.close()
        self.chan.close()
        self.ssh.close()
        g_logger.info(
            "Connection to %s:%d lost", self.dst_addr[0], self.dst_addr[1])

        clear_worker(self)
        g_logger.debug(clients)

""" Create a logger for logging in switchboar """

import logging

g_logger = logging.getLogger("inabox")

class CustomFormatter(logging.Formatter):
    """ Class formatter for logging """
    _grey = "\x1b[38;20m"
    _yellow = "\x1b[33;20m"
    _blue = "\x1b[34;20m"
    _green = "\x1b[32;20m"
    _red = "\x1b[31;20m"
    _bold_red = "\x1b[31;1m"
    _reset = "\x1b[0m"
    _format = "[%(levelname)s %(asctime)s %(funcName)s:%(lineno)d] "
    _message = "%(message)s"

    FORMATS = {
        logging.DEBUG: _blue + _format + _reset + _message,
        logging.INFO: _green + _format + _reset + _message,
        logging.WARNING: _yellow + _format + _reset + _message,
        logging.ERROR: _red + _format + _reset + _message,
        logging.CRITICAL: _bold_red + _format + _reset + _message
    }

    def format(self, record):
        """ returns logging desired format """
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logger(level=logging.DEBUG):
    """ Setup logger """

    # Log to a file
    handler = logging.FileHandler("inabox.log")
    handler.setFormatter(CustomFormatter())
    g_logger.addHandler(handler)

    # Log to the screen, too
    handler = logging.StreamHandler()
    handler.setFormatter(CustomFormatter())
    g_logger.addHandler(handler)

    g_logger.setLevel(level)

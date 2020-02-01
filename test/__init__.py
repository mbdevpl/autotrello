"""Initialization of tests of autotrello package."""

import logging

import colorlog

_HANDLER = logging.StreamHandler()
_HANDLER.setFormatter(colorlog.ColoredFormatter(
    '{name} [{log_color}{levelname}{reset}] {message}', style='{'))

logging.basicConfig(level=logging.DEBUG, handlers=[_HANDLER])
logging.getLogger().setLevel(logging.WARNING)
logging.getLogger('autotrello').setLevel(logging.DEBUG)

import logging

from .Client import Client
from .Errors import DiscroidError, LoginFailure
from .RequestHandler import RequestHandler
from .Utils import Utils
from .Websocket import Websocket

version = (1, 0, 0)

__all__ = (
    Client,
    DiscroidError,
    LoginFailure,
    RequestHandler,
    Utils,
    Websocket,
)
__title__ = "discroid"
__author__ = "Yas_!_ru"
__licence__ = "MIT"
__version__ = "{}.{}.{}v".format(*version)

logging.getLogger(__name__).addHandler(logging.NullHandler())

del logging

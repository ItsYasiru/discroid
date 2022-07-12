from __future__ import annotations

import asyncio
import json
import time
import zlib
from logging import getLogger
from typing import TYPE_CHECKING, NamedTuple

import aiohttp

from discroid.Abstracts import Cast, StateCast
from discroid.Casts import Message
from discroid.Errors import WebsocketClosure, WebsocketError

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop, Event, Future, Task
    from typing import Any, Awaitable, Callable, Optional

    from aiohttp import ClientWebSocketResponse

    from .Client import Client, State


logger = getLogger(__name__)


class OPCODE:
    DISPATCH = 0  # Receive         dispatches an event
    HEARTBEAT = 1  # Send/Receive    used for ping checking
    IDENTIFY = 2  # Send            used for client handshake
    PRESENCE_UPDATE = 3  # Send            used to update the client status
    VOICE_STATE_UPDATE = 4  # Send            used to join/move/leave voice channels
    VOICE_SERVER_PING = 5  # Send            used for voice ping checking
    RESUME = 6  # Send            used to resume a closed connection
    RECONNECT = 7  # Receive         used to tell when to reconnect (sometimes...)
    REQUEST_GUILD_MEMBERS = 8  # Send            used to request guild members (when searching for members in the search bar of a guild)
    INVALID_SESSION = 9  # Receive         used to notify client they have an invalid session id
    HELLO = 10  # Receive         sent immediately after connecting, contains heartbeat and server debug information
    HEARTBEAT_ACK = 11  # Sent            immediately following a client heartbeat that was received
    # GUILD_SYNC =                  12 # Receive         guild_sync but not used anymore
    DM_UPDATE = 13  # Send            used to get dm features
    LAZY_REQUEST = 14  # Send            discord responds back with GUILD_MEMBER_LIST_UPDATE type SYNC...
    LOBBY_CONNECT = 15  # ??
    LOBBY_DISCONNECT = 16  # ??
    LOBBY_VOICE_STATES_UPDATE = 17  # Receive
    STREAM_CREATE = 18  # ??
    STREAM_DELETE = 19  # ??
    STREAM_WATCH = 20  # ??
    STREAM_PING = 21  # Send
    STREAM_SET_PAUSED = 22  # ??
    REQUEST_APPLICATION_COMMANDS = 24  # Send            request application/bot cmds (user, message, and slash cmds)


class EVENTS:
    """Contains all the dispatched events and the data casts"""

    READY = None
    RESUMED = None
    MESSAGE_CREATE = Message


class EventListener(NamedTuple):
    check: Callable[[dict[str, Any]], bool]
    event: str
    result: Optional[Callable[[dict[str, Any]], Any]]
    future: asyncio.Future[Any]


class Heart:
    """Handles heartbeating"""

    def __init__(self, loop: AbstractEventLoop, wss: Websocket):
        self.wss: Websocket = wss
        self.loop: AbstractEventLoop = loop
        self.worker: Task = None

        self.last_heartbeat: float = None
        self.last_heartbeat_ack: float = None
        self.heartbeat_interval: int = None

    @property
    def latency(self):
        if all((self.last_heartbeat_ack, self.last_heartbeat)):
            return self.last_heartbeat_ack - self.last_heartbeat
        return float("inf")

    def ack(self):
        self.last_heartbeat_ack = time.perf_counter()

    async def start(self):
        payload = await self.wss.receive()

        if payload.get("op") == OPCODE.HELLO:
            data = payload.get("d", dict())
            self.heartbeat_interval: int = data.get("heartbeat_interval")

        async def worker():
            while True:
                await self.wss.send({"op": OPCODE.HEARTBEAT, "d": self.wss.last_sequence})
                self.last_heartbeat = time.perf_counter()
                await asyncio.sleep((self.heartbeat_interval) / 1000)

        self.worker = self.loop.create_task(worker())

    def stop(self):
        if self.worker:
            self.worker.cancel()


class Websocket:
    def __init__(
        self,
        api_version: int,
    ) -> None:
        self.is_ready: Event = None
        self.is_closed: bool = True
        self.session_id: str = None
        self.api_version = api_version
        self.last_sequence = None
        self.websocket_route: str = None

        self._state: State = None
        self.__heart: Heart = None
        self.__zlib = None
        self.__loop: AbstractEventLoop = None
        self.__websocket: ClientWebSocketResponse = None
        self.__dispatch_handlers: dict[str, list[Awaitable]] = dict()
        self.__dispatch_listeners: list[EventListener] = list()

    @property
    def latency(self) -> float:
        return self.__heart.latency

    @property
    def heartbeat_interval(self) -> float:
        return self.__heart.heartbeat_interval

    @staticmethod
    def get_websocket(
        base_url: str,
        api_version: int,
        *,
        zlib: bool = True,
        encoding: str = "json",
    ) -> str:
        if zlib:
            value = "{0}?encoding={1}&v={2}&compress=zlib-stream"
        else:
            value = "{0}?encoding={1}&v={2}"

        return value.format(base_url, encoding, api_version)

    @classmethod
    def prepare_payload(cls, op: int, /, data: dict) -> dict:
        return {"op": op, "d": data}

    def decompress(self, payload) -> dict:
        try:
            payload = self.__zlib.decompress(payload)
        except zlib.error:
            logger.error(f"error decompressing {payload}")

        return json.loads(payload.decode("UTF8"))

    async def send(self, payload: dict) -> None:
        logger.debug(f"sending {payload}")
        await self.__websocket.send_json(payload)

    async def receive(self) -> dict:
        payload = await self.__websocket.receive(self.heartbeat_interval)

        if payload.type is aiohttp.WSMsgType.BINARY:
            _json = self.decompress(payload.data)
            logger.debug(f"received {_json}")
            return _json
        elif payload.type is aiohttp.WSMsgType.ERROR:
            raise WebsocketError(payload.data)
        elif payload.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSE):
            raise WebsocketClosure
        else:
            logger.warn(f"unhandled websocket payload type {payload.type}")

    def register_listner(self, event: str, *, check: Callable[[dict[str, Any]], bool], result: Any = None, future: Future = None) -> Future:
        if not future:
            future = self.__loop.create_future()
        entry = EventListener(event=event, check=check, result=result, future=future)
        self.__dispatch_listeners.append(entry)
        return future

    def register_handler(self, event: str, *, func: Awaitable, cast_to: Any = None) -> None:
        handlers = self.__dispatch_handlers.get(event, list())
        handlers.append(func)
        self.__dispatch_handlers[event] = handlers

    async def hello(self) -> None:
        self.__heart = Heart(self.__loop, self)
        await self.__heart.start()

    async def ready(self, data: dict) -> None:
        self.is_ready.set()
        self.session_id = data.get("session_id")

    async def identify(self, token: str) -> None:
        payload = self.prepare_payload(
            OPCODE.IDENTIFY,
            {
                "token": token,
                "capabilities": 509,
                "properties": self._state.client.get_super_properties(),
                "presence": {"status": "online", "since": 0, "activities": list(), "afk": False},
                "compress": False,
                "client_state": {
                    "guild_hashes": dict(),
                    "highest_last_message_id": "0",
                    "read_state_version": 0,
                    "user_guild_settings_version": -1,
                    "user_settings_version": -1,
                },
            },
        )

        await self.send(payload)

    async def resume(self, token: str, session_id: str):
        payload = self.prepare_payload(
            OPCODE.RESUME,
            {
                "token": token,
                "session_id": session_id,
                "seq": 1337,
            },
        )
        await self.send(payload)

    async def setup(self, client: Client, *, websocket_route: str = None):
        self._state = client.get_state()

        self.websocket_route = websocket_route or self.get_websocket("wss://gateway.discord.gg/", self.api_version)

        self.is_ready = asyncio.Event()
        self.is_closed = False

        self._client: Client = client
        self.__zlib = zlib.decompressobj()
        self.__loop: AbstractEventLoop = self._state.loop
        self.__websocket: ClientWebSocketResponse = await self._state.http.connect_to_websocket(self.websocket_route)

    async def socket_loop(self):
        """A blocking call that runs the websocket"""
        while True:
            payload: dict = await self.receive()

            op: int = payload.get("op")
            data: dict = payload.get("d")
            event: str = payload.get("t")

            if op == OPCODE.HEARTBEAT_ACK:
                self.__heart.ack()

            if event == "READY":
                await self.ready(data)

            if data and event:
                cast: Cast = getattr(EVENTS, event, None)
                if cast:
                    if issubclass(cast, StateCast):
                        args = (data, self._state)
                    else:
                        args = (data,)
                    data = cast(*args)

                removed = list()
                for index, entry in enumerate(self.__dispatch_listeners):
                    if entry.event != event:
                        continue

                    future = entry.future
                    if future.cancelled():
                        removed.append(index)
                        continue

                    try:
                        valid = entry.check(data)
                    except Exception as exc:
                        future.set_exception(exc)
                        removed.append(index)
                    else:
                        if valid:
                            ret = data if entry.result is None else entry.result(data)
                            future.set_result(ret)
                            removed.append(index)

                for index in reversed(removed):
                    del self.__dispatch_listeners[index]

                if handlers := self.__dispatch_handlers.get(event):
                    for handler in handlers:
                        self.__loop.create_task(handler(data))

    async def connect(
        self,
        client: Client,
        token: str,
        *,
        reconnect: bool = True,
        reconnect_interval: int = 10,
        websocket_route: str = None,
        resume: str = None,
    ) -> None:
        async def post_setup():
            await self.setup(client, websocket_route=websocket_route)
            await self.hello()
            await self.identify(token)

            if resume or self.session_id:
                await self.resume(token, session_id=resume or self.session_id)

        if reconnect:
            while True:
                try:
                    await post_setup()
                    await self.socket_loop()
                except WebsocketClosure:
                    self.is_ready.clear()
                    self.is_closed = True

                logger.error("connection closed attempting reconnect")
                await asyncio.sleep(reconnect_interval)
        else:
            await post_setup()
            await self.socket_loop()

    async def close(self) -> None:
        if self.is_closed:
            return
        if self.__heart:
            self.__heart.stop()
        self.is_closed = True

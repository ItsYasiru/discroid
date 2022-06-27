from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from .RequestHandler import RequestHandler
from .User import User
from .Websocket import Websocket

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from typing import Awaitable, Optional

    from .Message import Message


class Client:
    def __init__(
        self,
        *,
        proxy: str = None,
        api_version: int = 9,
    ):
        self.api_version: int = api_version

        self.__wss: Websocket = None
        self.__http: RequestHandler = None
        self.__loop: AbstractEventLoop = None
        self.__proxy: str = proxy
        self.__setup_hook: Optional[Awaitable] = None

        self.user: User = None  # will be set after login

    async def __aenter__(self) -> None:
        await self.__setup_hook()

    async def __aexit__(self, *args, **kwargs) -> None:
        await self.close()

    async def close(self) -> None:
        await self.__wss.close()
        await self.__http.close()

    def setup_hook(self):
        def decorator(func):
            self.__setup_hook = func

        return decorator

    async def login(self, token: str) -> None:
        data = await self.__http.login(token.strip())
        self.user = User(data)

    async def send_message(self, channel_id: int, content: str) -> Message:
        return await self.__http.send_message(channel_id, content)

    async def trigger_typing(self, channel_id: int) -> None:
        return await self.__http.trigger_typing(channel_id)

    def run(self, token: str, *, reconnect: bool = True) -> None:
        self.__wss = Websocket(api_version=self.api_version)
        self.__http = RequestHandler(proxy=self.__proxy, api_version=self.api_version)

        async def runner():
            async with self:
                self.user = await self.__http.login(token=token)
                self.__wss = await self.__wss.connect(reconnect=reconnect)

        try:
            self.__loop = asyncio.get_event_loop()
            self.__loop.run_until_complete(runner())
        except KeyboardInterrupt:
            return
        except Exception as e:
            raise e

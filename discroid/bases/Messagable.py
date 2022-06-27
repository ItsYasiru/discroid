from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop, Task
    from typing import Generator

    from ..Client import Client


class Messagable:
    id: int

    _loop: AbstractEventLoop
    _client: Client

    async def send(self, *args, **kwargs):
        return await self._client.send_message(*args, **kwargs)

    def typing(self):
        return Typing(self)


class Typing:
    def __init__(self, messagable: Messagable):
        self.interval: int = 5
        self.messagable: Messagable = messagable

        self.__task: Task = None
        self.__loop: AbstractEventLoop = messagable._loop
        self.__client: Client = messagable._client

    def __await__(self) -> Generator:
        return self.__client.trigger_typing(self.messagable.id).__await__()

    async def __aenter__(self) -> None:
        def handle_future(future: asyncio.Future):
            try:
                future.exception()
            except (asyncio.CancelledError, Exception):
                pass

        async def worker() -> None:
            while True:
                await self.__client.trigger_typing(self.messagable.id)
                await asyncio.sleep(self.interval)

        self.__task = self.__loop.create_task(worker())
        self.__task.add_done_callback(handle_future)

    async def __aexit__(self, *args, **kwargs) -> None:
        self.__task.cancel()

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop, Task
    from types import TracebackType
    from typing import Generator, Optional, Type, TypeVar

    from ..Client import Client

    BE = TypeVar("BE", bound=BaseException)


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
        self.task: Task = None
        self.interval: int = 5
        self.messagable: Messagable = messagable

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

        self.task = self.__loop.create_task(worker())
        self.task.add_done_callback(handle_future)

    async def __aexit__(
        self,
        exc_type: Optional[Type[BE]],
        exc: Optional[BE],
        traceback: Optional[TracebackType],
    ) -> None:
        self.task.cancel()

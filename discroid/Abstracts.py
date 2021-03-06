from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asyncio import Task
    from typing import Generator

    from discroid.Casts import Message
    from discroid.Client import State


class Cast:
    """A class to cast JSON data to a functional python object"""

    pass


class StateCast(Cast):
    """Represensents a Cast that needs the client state"""

    _state: State


class Messagable(StateCast):
    id: int

    def __eq__(self, __o: object) -> bool:
        return self.id == __o.id if isinstance(__o, Messagable) else False

    def typing(self):
        return Typing(self, self._state)

    async def send(self, *args, **kwargs) -> Message:
        return await self._state.client.send_message(*args, **kwargs)


class Typing:
    def __init__(self, id: int, state: State):
        self.id: int = id
        self.interval: int = 5

        self._state: State = state
        self.__task: Task = None

    def __await__(self) -> Generator:
        return self._state.http.trigger_typing(self.id).__await__()

    async def __aenter__(self) -> None:
        def handle_future(future: asyncio.Future):
            try:
                future.exception()
            except (asyncio.CancelledError, Exception):
                pass

        async def worker() -> None:
            while True:
                await self._state.http.trigger_typing(self.id)
                await asyncio.sleep(self.interval)

        self.__task = self._state.loop.create_task(worker())
        self.__task.add_done_callback(handle_future)

    async def __aexit__(self, *args, **kwargs) -> None:
        self.__task.cancel()

from __future__ import annotations

from typing import TYPE_CHECKING

from .bases import Messagable

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

    from .Client import Client


class Channel(Messagable):
    def __init__(self, client: Client, data: dict):
        self.id: int = int(data.get("id"))

        self._loop: AbstractEventLoop = client._Client__loop
        self._client: Client = client


class ChannelMention:
    pass

from __future__ import annotations

from typing import TYPE_CHECKING

from discroid.Abstracts import Messagable, StateCast

if TYPE_CHECKING:
    from discroid.Client import State


class Channel(StateCast, Messagable):
    def __init__(self, data: dict, state: State):
        self.id: int = int(data.get("id"))

        self._state = state


class ChannelMention:
    pass

from __future__ import annotations

from typing import TYPE_CHECKING
from typing_extensions import Self

from discroid.Abstracts import Messagable

if TYPE_CHECKING:
    from discroid.Client import State


class TextChannel(Messagable):
    """Represents a text channel in a guild"""

    def __init__(self, data: dict, state: State):
        self.id: int = int(data.get("id"))

        self._state = state

    @classmethod
    def from_message(cls: Self, message_data: dict):
        """Returns a channel object by using data provided on a message"""
        data = {
            "id": message_data.get("channel_id"),
        }
        return cls(data)


class ChannelMention:
    pass

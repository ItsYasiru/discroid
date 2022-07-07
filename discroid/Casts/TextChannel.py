from __future__ import annotations

from typing import TYPE_CHECKING

from discroid.Abstracts import Messagable

if TYPE_CHECKING:
    from discroid.Client import State
    from typing_extensions import Self


class TextChannel(Messagable):
    """Represents a text channel in a guild"""

    def __init__(self, data: dict, state: State):
        self.id: int = int(data.get("id"))

        self._state = state

    @classmethod
    def from_message(cls: Self, message_data: dict, state: State) -> Self:
        """Returns a channel object by using data provided on a message"""
        data = {
            "id": message_data.get("channel_id"),
        }
        return cls(data, state)


class ChannelMention:
    pass

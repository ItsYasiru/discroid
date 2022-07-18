from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from discroid.Abstracts import StateCast
from discroid.Errors import IllegalArgumentError
from typing_extensions import Self

from .Embed import Embed
from .Reaction import Emoji, Reaction
from .Role import Role
from .TextChannel import ChannelMention, TextChannel
from .User import User

if TYPE_CHECKING:
    from typing import Optional

    from discroid.Client import State


class MessageReference(NamedTuple):
    guild_id: int
    channel_id: int
    message_id: int

    def to_dict(self) -> dict:
        return {
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "message_id": self.message_id,
        }

    @classmethod
    def from_message(cls, message: Message) -> Self:
        return cls(message.guild_id, message.channel_id, message.id)


class Message(StateCast):
    def __init__(self, data: dict, state: State):
        self.id: int = int(data.get("id"))
        self.tts: bool = data.get("tts", False)
        self.type: int = data.get("type")
        self.timestamp: str = data.get("timestamp")
        self.edited_timestamp: Optional[str] = _edited_timestamp if (_edited_timestamp := data.get("edited_timestamp")) else None

        self.author: User = User(data.get("author"), state)
        self.mentions: list[User] = [User(_user, state) for _user in data.get("mentions", list())]
        self.mention_roles: list[Role] = [Role(_role) for _role in data.get("mention_roles", list())]
        self.mention_channels: list[ChannelMention] = [ChannelMention(_mention) for _mention in data.get("mention_channels", list())]
        self.mention_everyone: bool = data.get("mention_everyone", False)

        self.embeds: list[Embed] = [Embed(_embed) for _embed in data.get("embeds", list())]
        self.reactions: list[Reaction] = [Reaction(_reaction, state) for _reaction in data.get("reactions", list())]
        self.attachemnts: Optional[list] = data.get("attachments")

        self.content: str = data.get("content")

        self.guild_id: Optional[int] = int(x) if (x := data.get("guild_id")) else None
        self.webhook_id: Optional[int] = int(x) if (x := data.get("webhoook_id")) else None
        self.channel_id: int = int(data.get("channel_id"))

        self._state: State = state
        self.__raw_data: dict = data

    def __str__(self) -> str:
        return self.content

    @property
    def channel(self):
        return TextChannel.from_message(self.__raw_data)

    async def reply(self, *args, **kwargs) -> Self:
        return await self._state.client.send_message(self.channel_id, *args, **kwargs, reference=MessageReference.from_message(self))

    async def react(
        self,
        reaction: Reaction = None,
        *,
        emoji: Emoji = None,
        emoji_id: int = None,
        emoji_name: str = None,
    ):
        if emoji is None and (emoji_id is None and emoji_name is None):
            raise IllegalArgumentError("provide either the arguments 'emoji' or 'emoji_id' and 'emoji_name")

        if not emoji and reaction:
            emoji = reaction.emoji

            if not emoji_id:
                emoji_id = emoji.id
            if not emoji_name:
                emoji_name = emoji.name

        return await self._state.http.react(
            self.channel_id,
            message_id=self.id,
            emoji_id=emoji_id,
            emoji_name=emoji_name,
        )

    async def delete_reaction(
        self,
        reaction: Reaction = None,
        *,
        user: User = None,
        user_id: int = None,
        emoji: Emoji = None,
        emoji_id: int = None,
        emoji_name: str = None,
    ) -> None:
        if reaction is None and emoji is None and not emoji_name:
            raise IllegalArgumentError("provide atleast one of the arguments 'reaction', 'emoji', or 'emoji_name'")

        if not emoji and reaction:
            emoji = reaction.emoji

            if not emoji_id:
                emoji_id = emoji.id
            if not emoji_name:
                emoji_name = emoji.name

        if user:
            user_id = user.id

        await self._state.http.react(
            self.channel_id,
            message_id=self.id,
            emoji_id=emoji_id,
            emoji_name=emoji_name,
            user_id=user_id,
            remove=True,
        )

    async def delete_all_reactions(self) -> None:
        await self._state.http.react(self.channel_id, message_id=self.id, remove_all=True)

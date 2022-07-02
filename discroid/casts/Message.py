from typing import TYPE_CHECKING

from .Channel import ChannelMention
from .Embed import Embed
from .Reaction import Reaction
from .Role import Role
from .User import User

if TYPE_CHECKING:
    from typing import Optional


class Message:
    def __init__(self, data: dict):
        self.id: int = int(data.get("id"))
        self.tts: bool = data.get("tts", False)
        self.type: int = data.get("type")
        self.timestamp: str = data.get("timestamp")
        self.edited_timestamp: Optional[str] = _edited_timestamp if (_edited_timestamp := data.get("edited_timestamp")) else None

        self.author: User = User(data.get("author"))
        self.mentions: list[User] = [User(_user) for _user in data.get("mentions", list())]
        self.mention_roles: list[Role] = [Role(_role) for _role in data.get("mention_roles", list())]
        self.mention_channels: list[ChannelMention] = [ChannelMention(_mention) for _mention in data.get("mention_channels", list())]
        self.mention_everyone: bool = data.get("mention_everyone", False)

        self.embeds: list[Embed] = [Embed(_embed) for _embed in data.get("embeds", list())]
        self.reactions: list[Reaction] = [Reaction(_reaction) for _reaction in data.get("reactions", list())]
        self.attachemnts = data.get("attachments")

        self.content: str = data.get("content")
        self.channel_id: int = int(data.get("channel_id"))

    def __str__(self) -> str:
        return self.content

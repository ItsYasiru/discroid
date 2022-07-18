from __future__ import annotations

from typing import TYPE_CHECKING

from discroid.Casts.User import User

if TYPE_CHECKING:
    from discroid.Client import State


class Emoji:
    def __init__(self, data: dict, state: State):
        self.id: int = int(x) if (x := data.get("id")) else None
        self.name: str = data.get("name")

        if self.id:
            self.roles: list[int] = [int(x) for x in x] if (x := data.get("roles")) else list()
            self.user: User = User(data.get("user"), state)
            self.available: bool = data.get("available", True)
            self.require_colons: bool = data.get("require_colons", False)
            self.managed: bool = data.get("managed", False)
            self.animated: bool = data.get("animated", False)


class Reaction:
    emoji: Emoji

    def __inti__(self, data: dict, state: State):
        self.count: int = int(data.get("count"))
        self.me: bool = data.get("me", False)
        self.emoji: Emoji = Emoji(data.get("emoji"), state)

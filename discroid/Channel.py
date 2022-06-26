from .bases import Messagable


class Channel(Messagable):
    def __init__(self, loop, client, data: dict):
        self.id: int = int(data.get("id"))

        self._loop = loop
        self._client = client


class ChannelMention:
    pass

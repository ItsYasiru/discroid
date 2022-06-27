class Websocket:
    def __init__(
        self,
        api_version: int,
    ) -> None:
        self.api_version = api_version
        self.websocket_route: str = None

    async def connect(self, client, *, websocket_route: str) -> None:
        self.websocket_route = websocket_route or self.get_websocket(
            "wss://gateway.discord.gg/", self.api_version
        )
        self.__loop = client._Client__loop
        self.__websocket = await client._Client__http.connect_to_websocket(
            self.websocket_route
        )

    async def close(self) -> None:
        pass

    @staticmethod
    def get_websocket(
        base_url: str,
        api_version: int,
        *,
        zlib: bool = True,
        encoding: str = "json",
    ) -> str:
        if zlib:
            value = "{0}?encoding={1}&v={2}&compress=zlib-stream"
        else:
            value = "{0}?encoding={1}&v={2}"

        return value.format(base_url, encoding, api_version)

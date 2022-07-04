from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, NamedTuple

import ua_parser.user_agent_parser

from discroid.Casts import ClientUser
from discroid.RequestHandler import RequestHandler
from discroid.Websocket import Websocket

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from typing import Any, Awaitable, Callable, Optional

    from discroid.Abstracts import Cast
    from discroid.Casts import Message


class State(NamedTuple):
    wss: Websocket
    http: RequestHandler
    loop: AbstractEventLoop
    client: Client


class Client:
    def __init__(self, *, proxy: str = None, locale: str = None, user_agent: str = None, api_version: int = 9, build_number: int = None):

        self.locale: str = locale or "en-US"
        self.user_agent: str = (
            user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"
        )
        self.build_number: int = build_number or 117300
        self.super_properties = self.get_super_properties()

        self.__wss = Websocket(api_version=api_version)
        self.__http = RequestHandler(self, proxy=proxy, api_version=api_version)
        self.__loop: AbstractEventLoop = None
        self.__state: State = State(self.__wss, self.__http, self.__loop, self)
        self.__setup_hook: Optional[Awaitable] = None

        self.user: ClientUser = None  # will be set after login

    @property
    def latency(self):
        return self.__wss.latency

    async def __aenter__(self) -> None:
        await self.__setup_hook() if self.__setup_hook else None

    async def __aexit__(self, *args, **kwargs) -> None:
        await self.close()

    async def close(self) -> None:
        await self.__wss.close()
        await self.__http.close()

    def setup(self):
        def decorator(func):
            self.__setup_hook = func
            return func

        return decorator

    def on(self, *, raw: bool = False):
        def decorator(func: Callable[[Cast]]) -> Callable:
            event: str = func.__name__.upper()
            self.__wss.register_handler(event, func=func)
            return func

        return decorator

    def event(self, event: str, *, raw: bool = False) -> Callable:
        def decorator(func: Callable[[Cast]]) -> Callable:
            self.__wss.register_handler(event, func=func)
            return func

        return decorator

    def wait_for(
        self,
        event: str,
        /,
        *,
        check: Callable[[dict[str, Any]], bool] = lambda *args, **kwargs: True,
        timeout: float = None,
    ) -> Any:
        future = self.__loop.create_future()
        self.__wss.register_listner(event=event, check=check, future=future)
        return asyncio.wait_for(future, timeout)

    async def login(self, token: str) -> None:
        data = await self.__http.login(token.strip())
        self.user = ClientUser(data)

    async def send_message(self, channel_id: int, content: str, *, reference: int = None) -> Message:
        return await self.__http.send_message(channel_id, content, message_reference=reference)

    async def trigger_typing(self, channel_id: int) -> None:
        return await self.__http.trigger_typing(channel_id)

    def run(self, token: str, *, reconnect: bool = True) -> None:
        async def runner():
            async with self:
                self.user = await self.__http.login(token, locale=self.locale, user_agent=self.user_agent)
                self.__wss = await self.__wss.connect(self, token=token, reconnect=reconnect)

        try:
            self.__loop = asyncio.get_event_loop()
            self.__loop.run_until_complete(runner())
        except KeyboardInterrupt:
            return
        except Exception as e:
            raise Exception(e)

    def get_super_properties(self):
        parsed_ua = ua_parser.user_agent_parser.Parse(self.user_agent)
        browser_versions = [parsed_ua["user_agent"]["major"], parsed_ua["user_agent"]["minor"], parsed_ua["user_agent"]["patch"]]
        os_versions = [parsed_ua["os"]["major"], parsed_ua["os"]["minor"], parsed_ua["os"]["patch"]]

        sp = {
            "os": parsed_ua["os"]["family"],
            "browser": parsed_ua["user_agent"]["family"],
            "device": "",
            "system_locale": self.locale,
            "browser_user_agent": parsed_ua["string"],
            "browser_version": ".".join(filter(None, browser_versions)),
            "os_version": ".".join(filter(None, os_versions)),
            "referrer": "",
            "referring_domain": "",
            "referrer_current": "",
            "referring_domain_current": "",
            "release_channel": "stable",
            "client_build_number": self.build_number,
            "client_event_source": None,
        }
        return sp

    def get_state(self) -> State:
        return self.__state

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

import aiohttp
import ua_parser.user_agent_parser

from discroid.casts import ClientUser, Message
from discroid.Utils import Utils

if TYPE_CHECKING:
    from typing import Any, Union

    from aiohttp import ClientWebSocketResponse


async def json_or_text(response: aiohttp.ClientResponse) -> Union[dict, str]:
    text = await response.text(encoding="utf-8")
    try:
        if response.headers["content-type"] == "application/json":
            return json.loads(text)
    except KeyError:
        pass

    return text


class RequestHandler:
    def __init__(
        self,
        *,
        api_version: int,
        retries: int = 3,
        proxy: str = None,
    ):
        self.retries: int = retries

        self.api_version: int = api_version
        self.base_route: str = f"https://discord.com/api/v{api_version}/"

        self.__proxy: str = proxy
        self.__headers: dict = None
        self.__session: aiohttp.ClientSession = aiohttp.ClientSession()

    async def set_headers(
        self,
        *,
        token: str,
        locale: str,
        user_agent: str,
        custom_headers: dict = None,
    ) -> None:
        parsed_ua = ua_parser.user_agent_parser.Parse(user_agent)
        self.__headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "{},{};q=0.9".format(locale, locale.split("-")[0]),
            "Authorization": token,
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "Pragma": "no-cache",
            "Referer": "https://discord.com/",
            "Sec-Ch-Ua": '" Not A;Brand";v="99", "Chromium";v="{0}", "Google Chrome";v="{0}"'.format(parsed_ua["user_agent"]["major"]),
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"{}"'.format(parsed_ua["os"]["family"]),
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": user_agent,
            "X-Debug-Options": "bugReporterEnabled",
            "X-Discord-Locale": locale,
            "Origin": "https://discord.com",
        }
        if custom_headers:
            self.__headers.update(custom_headers)

    async def request(
        self,
        method: str,
        route: str,
        json: dict = None,
        *,
        bind: Any = lambda x: x,
    ) -> Any:

        self.__headers["Referer"] = route

        kwargs = {
            "json": json or None,
            "proxy": self.__proxy,
            "headers": self.__headers,
        }

        for tries in range(self.retries):
            try:
                async with self.__session.request(method, self.base_route + route, **kwargs) as response:
                    data = await json_or_text(response)

                    if 300 > response.status >= 200:
                        return bind(data)

            except OSError as e:
                if tries < 4 and e.errno in (54, 10054):
                    await asyncio.sleep(1 + tries * 2)
                    continue
                raise

    async def close(self):
        await self.__session.close()

    async def login(
        self,
        token: str,
        *,
        locale: str = None,
        user_agent: str = None,
    ) -> ClientUser:
        await self.set_headers(token=token, locale=locale, user_agent=user_agent)
        return await self.request("GET", "/users/@me", bind=ClientUser)

    async def connect_to_websocket(
        self,
        route: str,
        *,
        compress: int = 0,
    ) -> ClientWebSocketResponse:
        kwargs = {
            "proxy": self.__proxy,
            "max_msg_size": 0,
            "timeout": 30.0,
            "autoclose": False,
            "headers": self.__headers,
            "compress": compress,
        }

        return await self.__session.ws_connect(route, **kwargs)

    async def send_message(
        self,
        channel_id: int,
        content: str,
        *,
        tts: bool = False,
        nonce=None,
        allowed_mentions=None,
        message_reference=None,
        sticker_ids=None,
    ) -> Message:
        json = {
            "tts": tts,
            "content": content,
        }
        if nonce == "calculate":
            nonce = Utils.calculate_nonce()
        else:
            nonce = str(nonce)
            json["nonce"] = nonce
        if message_reference is not None:
            json["message_reference"] = message_reference
        if allowed_mentions is not None:
            json["allowed_mentions"] = allowed_mentions
        if sticker_ids is not None:
            json["sticker_ids"] = sticker_ids

        route = f"/channels/{channel_id}/messages"
        return await self.request("POST", route, json=json, bind=Message)

    async def trigger_typing(self, channel_id: int) -> None:
        await self.request("POST", f"/channels/{channel_id}/typing")

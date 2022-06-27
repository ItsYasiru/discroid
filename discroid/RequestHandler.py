from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

import aiohttp
import ua_parser.user_agent_parser

from .Message import Message
from .User import ClientUser
from .Utils import Utils

if TYPE_CHECKING:
    from typing import Any, Union


async def json_or_text(response: aiohttp.ClientResponse) -> Union[dict, str]:
    text = await response.text(encoding="utf-8")
    try:
        if response.headers["content-type"] == "application/json":
            return json.loads(text)
    except KeyError:
        pass

    return text


class RequestHandler:
    def __init__(self, *, retries: int = 3, proxy: str = None):
        self.retries: int = retries

        self.api_version: int = 9
        self.base_route: str = f"https://discord.com/api/v{self.api_version}/"

        self.__proxy: str = proxy
        self.__headers: dict = None
        self.__session: aiohttp.ClientSession = aiohttp.ClientSession()

    async def set_headers(
        self,
        *,
        token: str,
        locale: str = None,
        user_agent: str = None,
        custom_headers: dict = None,
    ) -> None:
        if locale is None:
            locale = "en-US"
        if user_agent is None:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"

        parsed_ua = ua_parser.user_agent_parser.Parse(user_agent)
        self.__headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "{},{};q=0.9".format(locale, locale.split("-")[0]),
            "Authorization": token,
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "Pragma": "no-cache",
            "Referer": "https://discord.com/channels/@me",
            "Sec-Ch-Ua": '" Not A;Brand";v="99", "Chromium";v="{0}", "Google Chrome";v="{0}"'.format(
                parsed_ua["user_agent"]["major"]
            ),
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
        kwargs = {
            "json": json if json else None,
            "proxy": self.__proxy,
            "headers": self.__headers,
        }

        for tries in range(self.retries):
            try:
                async with self.__session.request(
                    method, self.base_route + route, **kwargs
                ) as response:
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

    async def send_message(
        self,
        channel_id: int,
        content: str,
        *,
        tts: bool = False,
        embed: dict = None,
        nonce=None,
        allowed_mentions=None,
        message_reference=None,
        sticker_ids=None,
    ) -> Message:
        json = {"content": content, "tts": tts}
        if nonce == "calculate":
            nonce = Utils.calculate_nonce()
        else:
            nonce = str(nonce)
            json["nonce"] = nonce
        if embed is not None:
            json["embed"] = embed
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

from __future__ import annotations

import asyncio
from json import loads
from logging import getLogger
from typing import TYPE_CHECKING

import aiohttp
import ua_parser.user_agent_parser

from discroid.Abstracts import Cast, StateCast
from discroid.Casts import ClientUser, Message
from discroid.Utils import Utils

if TYPE_CHECKING:
    from typing import Any

    from aiohttp import ClientWebSocketResponse

    from .Client import Client, State

logger = getLogger(__name__)


class RequestHandler:
    def __init__(
        self,
        *,
        proxy: str = None,
        retries: int = 3,
        cookies: Any = None,
        api_version: int = 9,
    ):
        self.retries: int = retries

        self.api_version: int = api_version
        self.base_route: str = f"https://discord.com/api/v{api_version}"

        self._state: State = None
        self.__proxy: str = proxy
        self.__headers: dict = None
        self.__cookies: Any = cookies
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
            "Referer": None,  # is set before every request
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
        /,
        route: str,
        json: dict = None,
        *,
        cast: Cast = None,
        custom_route: str = None,
    ) -> Any:
        route = self.base_route + route if not custom_route else custom_route
        self.__headers["Referer"] = route

        kwargs = {
            "json": json,
            "proxy": self.__proxy,
            "headers": self.__headers,
            "cookies": self.__cookies,
        }

        for tries in range(self.retries):
            try:
                async with self.__session.request(method, route, **kwargs) as response:
                    text = await response.text(encoding="utf-8")
                    data = text
                    try:
                        if response.headers["content-type"] == "application/json":
                            data = loads(text)
                    except KeyError:
                        pass

                    log_message = f"{response.status} {route} : {json} -> {data}"

                    if 300 > response.status >= 200:
                        logger.debug(log_message)
                        args = (data,)
                        if cast:
                            if issubclass(cast, StateCast):
                                args = (data, self._state)

                            return cast(*args)
                        return data
                    else:
                        logger.error(log_message)
                        break

            except OSError as e:
                if tries < 4 and e.errno in (54, 10054):
                    await asyncio.sleep(1 + tries * 2)
                    continue
                raise

    async def close(self):
        await self.__session.close()

    async def login(
        self,
        client: Client,
        token: str,
        *,
        locale: str = None,
        user_agent: str = None,
    ) -> ClientUser:
        self._state = client.get_state()

        await self.set_headers(token=token, locale=locale, user_agent=user_agent)
        return await self.request("GET", "/users/@me", cast=ClientUser)

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

    async def location_metadata(self):
        raise NotImplementedError

    async def survey(self):
        raise NotImplementedError

    async def maintenance_schedule(self):
        #  uses api v2
        raise NotImplementedError

    async def user_affinity_guilds(self):
        #  initial load of guilds I assume
        raise NotImplementedError

    async def user_library(self):
        #  discord's game library data
        raise NotImplementedError

    async def send_message(
        self,
        channel_id: int,
        /,
        content: str,
        *,
        tts: bool = False,
        sticker_ids: list[int] = None,
        allowed_mentions: list = None,
        message_reference: dict = None,
        nonce: str = None,
    ) -> Message:
        json = {
            "content": content,
            "nonce": nonce or Utils.calculate_nonce(),
            "tts": tts or False,
        }

        if sticker_ids:
            json["sticker_ids"] = sticker_ids
        if allowed_mentions:
            json["allowed_mentions"] = allowed_mentions
        if message_reference:
            json["message_reference"] = message_reference

        route = f"/channels/{channel_id}/messages"
        return await self.request("POST", route, json=json, cast=Message)

    async def trigger_typing(self, channel_id: int) -> None:
        await self.request("POST", f"/channels/{channel_id}/typing")

    async def interactions(
        self,
        interaction_type: int,
        /,
        application_id: int,
        *,
        guild_id: int,
        channel_id: int,
        options: list[dict] = [],
        attachments: list = [],
        command_id: int = None,
        command_name: str = None,
        command_type: int = None,
        command_version: int = None,
        command_description: str = None,
        permission: bool = True,
        dm_permission: bool = True,
        member_permissions: list = None,
        nonce: str = None,
    ):
        guild_id = str(guild_id)
        channel_id = str(channel_id)
        application_id = str(application_id)

        command_id = str(command_id)
        command_version = str(command_version or int(command_id) + 1)

        json = {
            "type": interaction_type,
            "application_id": application_id,
            "guild_id": guild_id,
            "channel_id": channel_id,
            "session_id": self._state.wss.session_id,
            "data": {
                "version": command_version,
                "id": command_id,
                "name": command_name,
                "type": command_type,
                "options": options,
                "attachments": attachments,
                "application_command": {
                    "id": command_id,
                    "application_id": application_id,
                    "version": command_version,
                    "default_permission": permission,
                    "default_memeber_permissions": member_permissions,
                    "type": command_type,
                    "name": command_name,
                    "description": command_description,
                    "dm_permission": dm_permission,
                    "options": options,
                },
            },
            "nonce": nonce or Utils.calculate_nonce(),
        }

        return await self.request("POST", "/interactions", json)

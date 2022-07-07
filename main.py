import logging
import logging.config
import os

import discroid
from discroid.Casts import Message

logging.config.fileConfig("./.conf/logging_test.conf")
logger = logging.getLogger(__name__)


def main() -> None:
    assert (TOKEN := os.getenv("TOKEN"))

    client = discroid.Client()

    @client.event("READY")
    async def on_ready(event):
        logger.debug("Client ready!")
        await client.trigger_slash_command(
            235148962103951360,
            guild_id=989193589319946290,
            channel_id=993468238539260025,
            command_id=988395626049982554,
            command_type=1,
            command_name="ping",
        )

    @client.event("MESSAGE_CREATE")
    async def on_message(message: Message):
        if message.author == client.user:
            return
        await message.reply("recv")

    @client.on()
    async def message_update(message):
        logger.debug(message)

    @client.on()
    async def message_delete(message):
        logger.debug(message)

    client.run(TOKEN)


if __name__ == "__main__":
    main()

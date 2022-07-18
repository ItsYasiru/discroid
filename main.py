import logging
import logging.config
import os

logging.config.fileConfig("./.conf/logging_test.conf")
logger = logging.getLogger(__name__)

import discroid  # noqa E402
from discroid.Casts import Message  # noqa E402


def main() -> None:
    assert (TOKEN := os.getenv("TOKEN"))

    client = discroid.Client(proxy="http://100.104.158.59:8080")

    async def test_command(message: Message):
        await message.reply("commmand invoked!")

    async def test_reactions(message: Message):
        EMOJI = r"%F0%9F%91%8D"
        await message.react(emoji_name=EMOJI)

        check = lambda d: int(d["message_id"]) == message.id and int(d["user_id"]) == message.author.id

        data = await client.wait_for("MESSAGE_REACTION_ADD", check=check)
        await message.delete_reaction(user_id=data["user_id"], emoji_name=EMOJI)

        data = await client.wait_for("MESSAGE_REACTION_ADD", check=check)
        await message.delete_all_reactions()

    async def test_slash_commands(message: Message):
        await client.trigger_slash_command(
            235148962103951360,
            guild_id=989193589319946290,
            channel_id=993468238539260025,
            command_id=988395626049982554,
            command_type=1,
            command_name="ping",
        )

    prefix = "!"
    commands = {
        "test": test_command,
        "react": test_reactions,
        "slash": test_slash_commands,
    }

    @client.event("READY")
    async def on_ready(event):
        logger.debug("Client ready!")

    @client.event("MESSAGE_CREATE")
    async def on_message(message: Message):
        if message.content.startswith(prefix):
            command = commands.get(message.content[1:])
            if command:
                await command(message)

    @client.on()
    async def message_update(message):
        logger.debug(message)

    @client.on()
    async def message_delete(message):
        logger.debug(message)

    client.run(TOKEN)


if __name__ == "__main__":
    main()

import os

import discroid
from discroid.Casts import Message


def main() -> None:
    assert (TOKEN := os.getenv("TOKEN"))

    client = discroid.Client()

    @client.event("READY")
    async def on_ready(event):
        print("Client ready!")
        _callback = await client.trigger_slash_command(2, 235148962103951360, guild_id=989193589319946290, channel_id=993468238539260025)
        _callback = await _callback(
            version=988395626049982555,
            command_id=988395626049982554,
            command_name="ping",
            command_type=1,
        )
        await _callback()

    @client.event("MESSAGE_CREATE")
    async def on_message(message: Message):
        if message.author == client.user:
            return
        await message.reply("recv")

    @client.on()
    def message_update(message):
        print(message)

    @client.on()
    async def message_delete(message):
        print(message)

    client.run(TOKEN)


if __name__ == "__main__":
    main()

import asyncio
import os

import discroid
from discroid.casts import Message


def main() -> None:
    # assert (PROXY := os.getenv("PROXY"))
    assert (TOKEN := os.getenv("TOKEN"))

    client = discroid.Client()

    @client.event("READY")
    async def on_ready(event):
        print("Client ready!")

    @client.event("MESSAGE_CREATE")
    async def on_message(message: Message):
        print("Message recieved!")
        print(client.latency)
        if message.author.id == client.user.id:
            return
        await client.trigger_typing(message.channel_id)
        await asyncio.sleep(2)
        await client.send_message(message.channel_id, message.content)

    client.run(TOKEN)


if __name__ == "__main__":
    main()

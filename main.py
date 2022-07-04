import os

import discroid
from discroid.Casts import Message


def main() -> None:
    assert (TOKEN := os.getenv("TOKEN"))

    client = discroid.Client()

    @client.event("READY")
    async def on_ready(event):
        print("Client ready!")

    @client.event("MESSAGE_CREATE")
    async def on_message(message: Message):
        if message.author == client.user:
            print(0)
            return
        print("Message recieved!")
        print(message)
        c = await client.send_message(message.channel_id, message.content)
        print(")", c, c.id)

    @client.on()
    async def message_create(message: Message):
        print(message.content)

    client.run(TOKEN)


if __name__ == "__main__":
    main()

import os
import discroid
from discroid import Channel


assert (TOKEN := os.getenv("TOKEN"))

client = discroid.Client()


@client.setup_hook()
async def test():
    channel = Channel(client, {"id": "989230366034366584"})

    async with channel.typing():
        msg = await client.send_message(989230366034366584, "Hello world!")
        print(msg)


client.run(TOKEN)

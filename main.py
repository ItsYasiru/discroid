import os
import discroid
from discroid import Channel


def main() -> None:
    assert (PROXY := os.getenv("PROXY"))
    assert (TOKEN := os.getenv("TOKEN"))

    client = discroid.Client(proxy=PROXY)

    @client.setup_hook()
    async def test():
        channel = Channel(client, {"id": "989230366034366584"})

        async with channel.typing():
            msg = await client.send_message(989230366034366584, "Hello world!")
            print(msg)

    client.run(TOKEN)


if __name__ == "__main__":
    main()

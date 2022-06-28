import os
import discroid


def main() -> None:
    assert (PROXY := os.getenv("PROXY"))
    assert (TOKEN := os.getenv("TOKEN"))

    client = discroid.Client(proxy=PROXY)

    @client.event("READY")
    async def on_ready(event):
        print(f"Client ready! {event}")

    @client.event("MESSAGE_CREATE")
    async def on_message(event):
        print(f"Message recieved! {event}")

    client.run(TOKEN)


if __name__ == "__main__":
    main()

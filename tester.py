import asyncio
import websockets

async def listen():
    url = "ws://127.0.0.1:7890"

    async with websockets.connect(url) as ws:
        while True:
            msg = await ws.recv()
            print(msg)

asyncio.new_event_loop().run_until_complete(listen())

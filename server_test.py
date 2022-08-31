import json
import asyncio
import websockets

from io import BytesIO
from PIL import Image


stream = BytesIO()
test_image = Image.open("/Users/lukasvasadi/Desktop/Images/cancer_cells.jpg")


async def start_stream(websocket):
    while True:
        test_image.save(stream, "jpeg")
        stream.seek(0)
        await websocket.send(stream.getvalue())
        # await asyncio.sleep(1)


async def server(websocket):
    async for msg in websocket:
        msg = json.loads(msg)
        print(msg)

        if msg["cmd"] == "stream":
            # await start_stream(websocket)
            asyncio.create_task(start_stream(websocket))

        # send confirmation
        msg = json.dumps(msg)
        await websocket.send(msg)


async def main():
    async with websockets.serve(server, "localhost", 8765):
        await asyncio.Future()  # run forever


asyncio.run(main())

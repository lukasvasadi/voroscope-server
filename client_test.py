import json
import asyncio
import websockets


async def send(websocket, msg):
    msg = json.dumps(msg)
    while True:
        await websocket.send(msg)
        # await asyncio.sleep(3)


async def receive(websocket):
    while True:
        msg = await websocket.recv()
        print(msg[:10])


async def main():
    async with websockets.connect("ws://localhost:8765") as websocket:
        msg0 = {"cmd": "gcode", "data": "G1 X5 Y10"}
        msg1 = {"cmd": "stream", "data": [200, 400]}

        await websocket.send(json.dumps(msg1))

        task0 = asyncio.create_task(send(websocket, msg0))
        task1 = asyncio.create_task(receive(websocket))

        # await send(websocket, msg1)
        # await receive(websocket)

        # await task0
        # await task1

        await send(websocket, msg1)
        await receive(websocket)


asyncio.run(main())

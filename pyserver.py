import json
import asyncio
import websockets

from io import BytesIO
from picamera import PiCamera
from serial import SerialException
from instructkey import InstructKey
from stage import Stage
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed


ADDRESS: str = "10.0.151.85"
PORT: int = 8765

stream = BytesIO()
camera = PiCamera()
stage = Stage(description="MARLIN", baudrate=115200, timeout=1.0)


async def cfg_camera(resolution: tuple = (640, 480), delay: float = 2.0):
    camera.resolution = resolution
    # Start camera preview and allow time for warm up
    camera.start_preview()
    await asyncio.sleep(delay)


async def get_frames(socket: WebSocketServerProtocol, delay: float = 0.05):
    # Capture with video port
    for _ in camera.capture_continuous(stream, "jpeg", use_video_port=True):
        try:
            await socket.send(stream.getvalue())  # send method is a coroutine
            stream.seek(0)
            stream.truncate()
            await asyncio.sleep(delay)
        except ConnectionClosed:
            print("Connection closed...")
            break


async def get_position(socket: WebSocketServerProtocol, delay: float = 1.0):
    while True:
        try:
            await stage.send("M114")
            response = await stage.recv()
            await socket.send(json.dumps({"pos": response}))
            await asyncio.sleep(delay)
        except ConnectionClosed:
            break
        except SerialException:
            await socket.send(json.dumps({"err": "Motherboard connection severed"}))
            break


async def handle_exchange(socket: WebSocketServerProtocol):
    async for message in socket:
        instruction: dict = json.loads(message)  # Convert message to dict
        for key in instruction.keys():
            match key:
                case InstructKey.RESOLUTION.value:
                    await cfg_camera(
                        tuple(instruction[key])
                    )  # Wait for camera setup before acquiring image stream
                    # NOTE: Tasks can be cancelled manually!
                    asyncio.create_task(get_frames(socket))
                    asyncio.create_task(get_position(socket))
                case InstructKey.GCODE.value:
                    await stage.send(instruction[key])
                case _:
                    await socket.send(
                        json.dumps({"err": f"Unrecognized instruction: {key}"})
                    )


async def main():
    async with websockets.serve(handle_exchange, ADDRESS, PORT):
        await asyncio.Future()  # Run forever


asyncio.run(main())

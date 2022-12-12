import json
import asyncio
import websockets

from io import BytesIO
from picamera import PiCamera
from motherboard import Motherboard


# Test image
PATH_TEST_IMG = "images/hela-cells.jpg"

stream = BytesIO()
camera = PiCamera()

port = Motherboard.get_port(description="MARLIN")
skr = Motherboard(port=port, baudrate=115200)


async def set_camera(resolution: tuple = (640, 480)):
    camera.resolution = resolution
    # start a preview and let the camera warm up for 2 seconds
    camera.start_preview()
    # wait for the camera to settle before proceeding
    await asyncio.sleep(2)


async def stream_images(websocket):
    # capture with video port
    for _ in camera.capture_continuous(stream, "jpeg", use_video_port=True):
        await websocket.send(stream.getvalue())
        stream.seek(0)
        stream.truncate()


async def handle_exchange(websocket):
    async for message in websocket:
        message = json.loads(message)
        print(message)
        if "resolution" in message.keys():
            # Wait for configuration before running image stream
            await set_camera(tuple(message["resolution"]))
            # Start image stream
            task = asyncio.create_task(stream_images(websocket))
        elif "gcode" in message.keys():
            print(message["gcode"])
            skr.send(message["gcode"])


async def main():
    async with websockets.serve(handle_exchange, "10.0.151.85", 8765):
        await asyncio.Future()  # Run forever


asyncio.run(main())

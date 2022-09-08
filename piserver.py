import json
import asyncio
import websockets

from io import BytesIO
from picamera import PiCamera


# test image
IMG_PATH = "/home/voroscope/Desktop/hela-cells.jpg"

stream = BytesIO()
camera = PiCamera()


async def configure_camera(resolution: tuple = (640, 480)):
    camera.resolution = resolution
    # start a preview and let the camera warm up for 2 seconds
    camera.start_preview()
    # wait for the camera to settle before proceeding
    await asyncio.sleep(2)


async def collect_images(websocket):
    # capture with video port
    for _ in camera.capture_continuous(stream, "jpeg", use_video_port=True):
        await websocket.send(stream.getvalue())
        stream.seek(0)
        stream.truncate()


async def manage(websocket):
    async for message in websocket:
        message = json.loads(message)
        print(message)
        if "resolution" in message.keys():
            # wait for configuration to finish before running camera stream
            await configure_camera(tuple(message["resolution"]))
            # now that camera is configured, run stream
            task = asyncio.create_task(collect_images(websocket))
        elif "gcode" in message.keys():
            print(message["gcode"])


async def main():
    async with websockets.serve(manage, "10.0.151.85", 8765):
        await asyncio.Future()  # run forever


asyncio.run(main())

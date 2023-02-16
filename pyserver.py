import json
import asyncio
import websockets

from stage import Stage
from camera import Camera
from instructions import Key
from typing import Callable
from multiprocessing import Process
from argparse import ArgumentParser
from websockets.server import WebSocketServerProtocol


parser = ArgumentParser()
parser.add_argument("-a", "--Address", help="Server address")
parser.add_argument("-c", "--Camera", help="Camera port")
parser.add_argument("-s", "--Stage", help="Stage port")

args = parser.parse_args()

ADDRESS = args.Address if args.Address else "10.0.151.85"
CAMERA_PORT = args.Camera if args.Camera else 8765
STAGE_PORT = args.Stage if args.Stage else 8775


async def handle_camera(socket: WebSocketServerProtocol):
    global camera
    camera = Camera()
    async for message in socket:
        instruction: dict = json.loads(message)  # Convert message to dict
        for key in instruction.keys():
            match key:
                case Key.RESOLUTION.value:
                    try:
                        # camera = Camera(resolution=tuple(instruction[key]))
                        camera.resolution = tuple(instruction[key])
                    except:
                        camera.resolution = tuple(instruction[key])
                    await camera.startup()

                    # NOTE: Tasks can be cancelled manually!
                    task = asyncio.create_task(camera.get_frames(socket))
                    await task

                    if task.exception():
                        print(f"Warning: Received {task.exception()} from camera")
                case _:
                    await socket.send(
                        json.dumps({"err": f"Unrecognized instruction: {key}"})
                    )


async def handle_stage(socket: WebSocketServerProtocol):
    global stage
    stage = Stage(description="MARLIN", baudrate=115200, timeout=1.0)
    async for message in socket:
        instruction: dict = json.loads(message)  # Convert message to dict
        for key in instruction.keys():
            match key:
                case Key.POSITION.value:
                    asyncio.create_task(stage.get_position(socket))
                case Key.GCODE.value:
                    await stage.send(instruction[key])
                case _:
                    await socket.send(
                        json.dumps({"err": f"Unrecognized instruction: {key}"})
                    )


def cfg_websocket(handle: Callable, address: str, port: int):
    async def main():
        async with websockets.serve(handle, address, port):
            await asyncio.Future()  # Run forever

    asyncio.run(main())


if __name__ == "__main__":
    camera_proc = Process(
        target=cfg_websocket, args=(handle_camera, ADDRESS, CAMERA_PORT)
    )

    stage_proc = Process(target=cfg_websocket, args=(handle_stage, ADDRESS, STAGE_PORT))

    camera_proc.start()
    stage_proc.start()

    camera_proc.join()
    stage_proc.join()

    camera.close()
    stage.close()

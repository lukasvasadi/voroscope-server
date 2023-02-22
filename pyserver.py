import json
import asyncio
import websockets

from stage import Stage
from camera import Camera
from instructions import CameraKey, StageKey

from typing import Callable
from multiprocessing import Process
from argparse import ArgumentParser
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedError


# Setup optional command line arguments
parser = ArgumentParser()
parser.add_argument("-a", "--address", help="Server address")
parser.add_argument("-c", "--cameraport", help="Camera port")
parser.add_argument("-s", "--stageport", help="Stage port")

args = parser.parse_args()

# Load default websocket configuration
defaults = json.load(open("settings.json"))

ADDRESS = args.address if args.address else defaults["address"]
CAMERAPORT = args.cameraport if args.cameraport else defaults["cameraport"]
STAGEPORT = args.stageport if args.stageport else defaults["stageport"]


async def handle_camera(socket: WebSocketServerProtocol, camera: Camera):
    camera = Camera()
    try:
        async for message in socket:
            instruction: dict = json.loads(
                message
            )  # Convert json serialized message to dict
            for key in instruction.keys():
                match key:
                    case CameraKey.CFG.value:
                        camera.resolution = tuple(instruction[key]["resolution"])
                        await camera.startup()

                        # NOTE: Tasks can be cancelled manually!
                        task = asyncio.create_task(camera.get_frames(socket))
                        # await task

                        # if task.exception():
                        #     print(f"Warning: Camera raised {task.exception()}")
                    case _:
                        await socket.send(
                            json.dumps({"err": f"Unrecognized instruction: {key}"})
                        )
    except ConnectionClosedError:
        pass
    finally:
        camera.close()


async def handle_stage(socket: WebSocketServerProtocol, stage: Stage):
    stage = Stage()
    try:
        async for message in socket:
            instruction: dict = json.loads(
                message
            )  # Convert json serialized message to dict
            for key in instruction.keys():
                match key:
                    case StageKey.POS.value:
                        asyncio.create_task(
                            stage.get_position(socket, instruction[key])
                        )
                    case StageKey.CMD.value:
                        print(instruction[key])
                        await stage.send(instruction[key])
                    case _:
                        await socket.send(
                            json.dumps({"err": f"Unrecognized instruction: {key}"})
                        )
    except ConnectionClosedError:
        pass
    finally:
        stage.close()


def cfg_websocket(handle: Callable, address: str, port: int):
    async def main():
        async with websockets.serve(handle, address, port):
            await asyncio.Future()  # Run forever

    asyncio.run(main())


if __name__ == "__main__":
    camera_proc = Process(
        target=cfg_websocket, args=(handle_camera, ADDRESS, CAMERAPORT)
    )

    stage_proc = Process(target=cfg_websocket, args=(handle_stage, ADDRESS, STAGEPORT))

    # Run isolated processes
    camera_proc.start()
    stage_proc.start()

    # Join processes before exit
    camera_proc.join()
    stage_proc.join()

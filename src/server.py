# ===============================================================================
#   Server configuration for Voroscope platform
#   Websockets API reference: https://websockets.readthedocs.io/en/stable/reference/index.html
# ===============================================================================

import json
import asyncio
import websockets

import websockets.server as server

from asyncio import Task
from typing import Optional
from typing import Callable
from argparse import ArgumentParser
from multiprocessing import Process
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from stage import Stage
from camera import Camera
from instructions import CameraKey, StageKey


# Setup optional command line arguments
parser = ArgumentParser()
parser.add_argument("-a", "--address", help="Server address")
parser.add_argument("-c", "--camera", help="Camera port")
parser.add_argument("-s", "--stage", help="Stage port")

args = parser.parse_args()

# Load default websocket configuration
defaults = json.load(open("settings.json"))

ADDRESS = args.address if args.address else defaults["address"]
CAMERA_PORT = args.cameraport if args.cameraport else defaults["ports"]["camera"]
STAGE_PORT = args.stageport if args.stageport else defaults["ports"]["stage"]


async def process_task_cancellation(task: Task) -> None:
    print(f"Camera coroutine cancellation request status: {task.cancel()}")
    await asyncio.sleep(0.1)  # Allow asyncio to process cancellation
    print(f"Camera coroutine cancellation status: {task.cancelled()}")

    if task.exception():
        print(f"Warning: Camera coroutine raised {task.exception()}")


async def handle_camera(socket: server.WebSocketServerProtocol, camera: Camera):
    task: Optional[Task] = None
    try:
        camera = Camera()
        async for message in socket:
            data = json.loads(message)  # Convert json serialized message to dict
            for key in data.keys():
                match key:
                    case CameraKey.CFG.value:
                        camera.resolution = tuple(data[key]["resolution"])
                        await camera.startup()

                        task = asyncio.create_task(camera.get_frames(socket))
                    case _:
                        await socket.send(
                            json.dumps({"err": f"Unrecognized instruction: {key}"})
                        )
    except (ConnectionClosedError, ConnectionClosedOK, KeyboardInterrupt):
        if task is not None:
            await process_task_cancellation(task)
    finally:
        print("Closing camera...")
        camera.close()


async def handle_stage(socket: server.WebSocketServerProtocol, stage: Stage):
    task: Optional[Task] = None
    try:
        stage = Stage()
        async for message in socket:
            instruction: dict = json.loads(
                message
            )  # Convert json serialized message to dict
            for key in instruction.keys():
                match key:
                    case StageKey.POS.value:
                        task = asyncio.create_task(
                            stage.get_position(socket, int(instruction[key]))
                        )
                    case StageKey.CMD.value:
                        print(instruction[key])
                        await stage.send(instruction[key])
                    case _:
                        await socket.send(
                            json.dumps({"err": f"Unrecognized instruction: {key}"})
                        )
    except (ConnectionClosedError, ConnectionClosedOK, KeyboardInterrupt):
        if task is not None:
            await process_task_cancellation(task)
    finally:
        print("Closing stage...")
        stage.close()


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

    # Run isolated processes
    camera_proc.start()
    stage_proc.start()

    try:
        # Join processes before exit
        camera_proc.join()
        stage_proc.join()
    except KeyboardInterrupt:
        camera_proc.terminate()
        stage_proc.terminate()
        print("Processes terminated with KeyboardInterrupt")

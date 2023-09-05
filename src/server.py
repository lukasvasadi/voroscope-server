# ===============================================================================
#   Server configuration for Voroscope platform
#   Websockets API reference: https://websockets.readthedocs.io/en/stable/reference/index.html
# ===============================================================================

import json
import asyncio
import websockets

import websockets.server as server
import websockets.exceptions as exceptions

from enum import Enum
from asyncio import Task
from argparse import ArgumentParser
from multiprocessing import Process
from typing import Optional, Callable

from src.stage import Stage
from src.camera import Camera

from termcolor import colored


class Instruction(Enum):
    CFG = 0
    CMD = 1
    POS = 2


# Setup optional command line arguments
parser = ArgumentParser()
parser.add_argument("-a", "--address", help="Server address")
parser.add_argument("-c", "--camera", help="Camera port")
parser.add_argument("-s", "--stage", help="Stage port")

args = parser.parse_args()

# Load default websocket configuration
defaults = json.load(open("config/settings.json"))

ADDRESS = args.address if args.address else defaults["address"]
CAMERA_PORT = args.camera if args.camera else defaults["ports"]["camera"]
STAGE_PORT = args.stage if args.stage else defaults["ports"]["stage"]


async def process_task_cancellation(task: Task) -> None:
    print(
        colored(
            f"Camera coroutine cancellation request: {task.cancel()}",
            "magenta",
            attrs=["bold"],
        )
    )
    await asyncio.sleep(0.1)  # Allow asyncio to process cancellation
    print(
        colored(
            f"Camera coroutine cancellation status: {task.cancelled()}",
            "magenta",
            attrs=["bold"],
        )
    )

    if task.exception():
        print(
            colored(
                f"Warning: Camera coroutine exception: {task.exception()}",
                "red",
                attrs=["bold"],
            )
        )


async def handle_camera(socket: server.WebSocketServerProtocol, camera: Camera):
    task: Optional[Task] = None
    data: dict
    key: str
    try:
        camera = Camera(socket)
        print(colored("Camera connected", "green", attrs=["bold"]))
        async for message in socket:
            data = json.loads(message)  # Convert json serialized message to dict
            for key in data.keys():
                match key.upper():
                    case Instruction.CFG.name:
                        camera.resolution = tuple(data[key]["resolution"])
                        await camera.startup()
                        task = asyncio.create_task(camera.get_frames())
                    case _:
                        await socket.send(
                            json.dumps({"err": f"Unrecognized instruction: {key}"})
                        )
    except (
        exceptions.ConnectionClosedError,
        exceptions.ConnectionClosedOK,
        KeyboardInterrupt,
    ):
        if task is not None:
            await process_task_cancellation(task)
    finally:
        print(colored("Closing camera...", "yellow", attrs=["bold"]))
        camera.close()


async def handle_stage(socket: server.WebSocketServerProtocol, stage: Stage):
    task: Optional[Task] = None
    data: dict
    key: str
    try:
        stage = Stage(socket)
        print(colored("Stage connected", "green", attrs=["bold"]))
        async for message in socket:
            data = json.loads(message)  # Convert json serialized message to dict
            for key in data.keys():
                match key.upper():
                    case Instruction.POS.name:
                        task = asyncio.create_task(stage.get_position(int(data[key])))
                    case Instruction.CMD.name:
                        print(data[key])
                        await stage.send(data[key])
                    case _:
                        await socket.send(
                            json.dumps({"err": f"Unrecognized instruction: {key}"})
                        )
    except (
        exceptions.ConnectionClosedError,
        exceptions.ConnectionClosedOK,
        KeyboardInterrupt,
    ):
        if task is not None:
            await process_task_cancellation(task)
    finally:
        print(colored("Closing camera...", "yellow", attrs=["bold"]))
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

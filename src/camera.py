import asyncio

import websockets.server as server
import websockets.exceptions as exceptions

from io import BytesIO

try:
    from picamera import PiCamera
except ModuleNotFoundError:
    raise RuntimeError("Camera object can only be instantiated for Raspberry Pi")


class Camera(PiCamera):
    """Connection to Raspberry Pi High Quality camera module"""

    def __init__(
        self, socket: server.WebSocketServerProtocol, resolution: tuple = (640, 480)
    ):
        super().__init__(resolution=resolution)

        self.socket = socket

    async def startup(self, delay: float = 2.0) -> None:
        """Allow time to warm up"""

        self.start_preview()
        await asyncio.sleep(delay)

    async def get_frames(self) -> None:
        """Transmit frames from continuous capture with video port"""

        stream = BytesIO()

        try:
            for _ in self.capture_continuous(stream, "jpeg", use_video_port=True):
                try:
                    await self.socket.send(
                        stream.getvalue()
                    )  # send method is a coroutine
                    stream.seek(0)
                    stream.truncate()
                    # await asyncio.sleep(0.01)
                except (exceptions.ConnectionClosed, exceptions.ConnectionClosedOK):
                    return
        except (KeyError, AttributeError):
            return

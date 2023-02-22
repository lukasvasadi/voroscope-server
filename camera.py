import asyncio

from io import BytesIO
from picamera import PiCamera
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK


class Camera(PiCamera):
    """Connection to Raspberry Pi High Quality camera module"""

    def __init__(self, resolution: tuple = (640, 480)):
        super().__init__(resolution=resolution)

        self.image_stream = BytesIO()

    async def startup(self, delay: float = 2.0) -> None:
        """Allow time to warm up"""

        self.start_preview()
        await asyncio.sleep(delay)

    async def get_frames(
        self, socket: WebSocketServerProtocol, delay: float = 0.01
    ) -> None:
        """Transmit frames from continuous capture with video port"""

        try:
            for _ in self.capture_continuous(
                self.image_stream, "jpeg", use_video_port=True
            ):
                try:
                    await socket.send(
                        self.image_stream.getvalue()
                    )  # send method is a coroutine
                    self.image_stream.seek(0)
                    self.image_stream.truncate()
                    await asyncio.sleep(delay)
                except (ConnectionClosed, ConnectionClosedOK):
                    return
        except (KeyError, AttributeError):
            print("Camera experienced an unexpected cancel request")

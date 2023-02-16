import asyncio

from io import BytesIO
from picamera import PiCamera
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed


class Camera(PiCamera):
    """Connection to Raspberry Pi High Quality camera module"""

    def __init__(self, resolution: tuple = (640, 480), startup_delay: float = 2.0):
        super().__init__(resolution=resolution)

        self.startup_delay = startup_delay
        self.image_stream = BytesIO()

    async def startup(self) -> None:
        """Allow time to warm up"""

        self.start_preview()
        await asyncio.sleep(self.startup_delay)

    async def get_frames(
        self, socket: WebSocketServerProtocol, delay: float = 0.05
    ) -> None:
        """Continuous capture with video port"""

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
            except ConnectionClosed:
                print("Connection closed...")
                return
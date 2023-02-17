import json
import serial
import asyncio

from serial import Serial, SerialException
from serial.tools import list_ports as ports
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed


class Stage(Serial):
    """Serial connection to BTT SKR Mini E3"""

    def __init__(
        self, description: str = "MARLIN", baudrate: int = 115200, timeout: float = 1.0
    ):
        super().__init__(
            port=self.__get_port(description), baudrate=baudrate, timeout=timeout
        )

        self.parity = serial.PARITY_NONE
        self.stopbits = serial.STOPBITS_ONE
        self.xonxoff = False
        self.rtscts = False
        self.dsrdtr = False

    @staticmethod
    def __get_descriptions() -> list:
        """Return list of connected serial port descriptions"""

        return [comport.description for comport in ports.comports()]

    @staticmethod
    def __get_port(description) -> str:
        """Use string description to locate serial port"""

        try:
            return [
                comport.device
                for comport in ports.comports()
                if description in comport.description
            ][0]
        except IndexError:
            return None

    def reset_buffers(self) -> None:
        """Reset transmission input and output buffers"""

        self.reset_input_buffer()
        self.reset_output_buffer()

    async def send(self, data: str) -> None:
        """Send bytearray to device"""

        data += "\r"

        self.reset_buffers()  # Flush
        self.write(data.encode())  # Pass as bytearray

    async def recv(self) -> str:
        """Read incoming data and decode"""

        return self.readline().decode("utf-8", "ignore").strip()

    async def get_position(
        self, socket: WebSocketServerProtocol, delay: float = 1.0
    ) -> None:
        """Transmit current stage position"""

        while True:
            try:
                await self.send("M114")
                response = await self.recv()
                await socket.send(json.dumps({"pos": response}))
                await asyncio.sleep(delay)
            except ConnectionClosed:
                return
            except SerialException:
                await socket.send(json.dumps({"err": "Motherboard connection severed"}))
                return

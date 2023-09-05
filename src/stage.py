import json
import serial
import asyncio

import websockets.server as server
import websockets.exceptions as exceptions

from typing import Optional
from serial import Serial, SerialException
from serial.tools import list_ports as ports


class Stage(Serial):
    """Serial connection to BTT SKR Mini E3

    Default timeout to None, i.e., wait forever until requested bytes received
    """

    def __init__(
        self,
        socket: server.WebSocketServerProtocol,
        description: str = "MARLIN",
        baudrate: int = 115200,
        timeout: Optional[float] = None,
    ):
        super().__init__(
            port=self.__get_port(description), baudrate=baudrate, timeout=timeout
        )

        self.parity = serial.PARITY_NONE
        self.stopbits = serial.STOPBITS_ONE
        self.xonxoff = False
        self.rtscts = False
        self.dsrdtr = False

        self.socket = socket

    @staticmethod
    def __get_descriptions() -> list:
        """Return list of connected serial port descriptions"""

        return [comport.description for comport in ports.comports()]

    @staticmethod
    def __get_port(description) -> Optional[str]:
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

    async def send(self, data: str, encoding: str = "utf-8") -> None:
        """Send bytearray to device"""

        data += "\r"

        self.write(data.encode(encoding))  # Pass as bytearray
        self.flush()

    async def recv(self, encoding: str = "utf-8") -> str:
        """Read incoming data and decode"""

        return self.readline().decode(encoding, "ignore").strip()

    async def get_position(self, interval: int = 1) -> None:
        """Transmit current stage position

        https://marlinfw.org/docs/gcode/M154.html
        """

        await self.send(f"M154 S{interval}")  # Enable auto-report

        while True:
            try:
                response = await self.recv()  # Wait until bytes received

                if any([axis in response for axis in ("X", "Y", "Z")]):
                    await self.socket.send(json.dumps({"pos": response}))

                    # NOTE: A delay is needed to prevent serial port blocking
                    await asyncio.sleep(interval)
                elif response in ("ok", "echo:busy: processing"):
                    continue
                else:
                    await self.socket.send(json.dumps({"err": response}))
            except (exceptions.ConnectionClosed, exceptions.ConnectionClosedOK):
                await self.send("M154 S0")  # Disable auto-report
                return
            except SerialException:
                return

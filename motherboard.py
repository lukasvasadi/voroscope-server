import serial
from serial import Serial
from serial.tools import list_ports


class Motherboard(Serial):
    """Serial connection to BTT SKR Mini E3"""

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0):
        super().__init__(port=port, baudrate=baudrate, timeout=timeout)

        self.parity = serial.PARITY_NONE
        self.stopbits = serial.STOPBITS_ONE
        self.xonxoff = False
        self.rtscts = False
        self.dsrdtr = False

    @staticmethod
    def get_port_descriptions() -> list:
        """Return list of connected serial port descriptions"""

        return [comport.description for comport in list(list_ports.comports())]

    @staticmethod
    def get_port(description) -> str:
        """Use text description to automatically locate serial port"""

        try:
            return [
                comport.device
                for comport in list(list_ports.comports())
                if description in comport.description
            ][0]
        except IndexError:
            return None

    def reset_buffers(self) -> None:
        """Reset transmission input and output buffers"""

        self.reset_input_buffer()
        self.reset_output_buffer()

    def send(self, data: str) -> None:
        """Send bytearray to device"""

        data = data + "\r"

        self.reset_buffers()  # Flush
        self.write(data.encode())  # Pass as bytearray

    def receive(self) -> str:
        """Read incoming data and decode"""

        return self.readline().decode("utf-8", "ignore").strip()

    def close_port(self) -> None:
        """Safely close serial port"""

        if self.is_open:
            self.close()

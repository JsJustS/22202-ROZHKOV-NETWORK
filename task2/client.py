import network
from os import path
import logging


class Client(network.App):
    def __init__(self, host: str, port: int, filepath: str):
        super().__init__(host, port)
        self.filepath = filepath
        if not path.exists(self.filepath):
            raise FileNotFoundError(self.filepath)
        if path.isdir(self.filepath):
            raise IsADirectoryError(self.filepath)

    def start(self) -> None:
        super().start()
        self._socket.connect((self.host, self.port))
        logging.debug(f"Client connected to {self.host}:{self.port}")

        self._socket.send(bytes(network.PacketGenerator(path.basename(self.filepath).encode("UTF-8"))))
        self._socket.send(bytes(network.PacketGenerator(path.getsize(self.filepath))))
        with open(self.filepath, "rb") as f:
            file = f.read()
            # print(file)
            self._socket.send(bytes(network.PacketGenerator(file)))

import network
from os import path
import logging


logging.basicConfig(
    format="%(levelname)s: [%(threadName)s] > %(message)s",
    level=logging.DEBUG
)


class Client(network.App):
    def __init__(self, host: str, port: int, filepath: str, packet_size: int = 4096):
        super().__init__(host, port)
        self.filepath = filepath
        self.packet_size = packet_size
        if not path.exists(self.filepath):
            raise FileNotFoundError(self.filepath)
        if path.isdir(self.filepath):
            raise IsADirectoryError(self.filepath)

    def start(self) -> None:
        super().start()
        self._socket.connect((self.host, self.port))
        logging.info(f"Client connected to {self.host}:{self.port}")

        self.handleFileTransaction()

    def sendFile(self):
        with open(self.filepath, "rb") as f:
            for piece in network.PacketGenerator(f.read(), length=self.packet_size).generatePieces():
                self._send(piece)

    def handleFileTransaction(self):
        self.send(path.basename(self.filepath).encode("UTF-8"))
        logging.debug(f"Client sent filename \"{path.basename(self.filepath)}\"")

        self.send(path.getsize(self.filepath))
        logging.debug(f"Client sent file size \"{path.getsize(self.filepath)} byte(s)\"")

        logging.debug(f"Client started sending file...")
        self.sendFile()
        logging.debug(f"Client finished transaction!")

        status_b = self.receive()
        is_transaction_successful = bool.from_bytes(status_b, "big")
        if is_transaction_successful:
            logging.info("Transaction successful.")
        else:
            logging.info("Transaction incomplete.")

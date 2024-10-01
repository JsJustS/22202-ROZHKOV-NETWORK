import network
from os import path
import logging


logging.basicConfig(
    format="%(levelname)s: [%(threadName)s] > %(message)s",
    level=logging.DEBUG
)


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
        logging.info(f"Client connected to {self.host}:{self.port}")

        self.handleFileTransaction()

    def handleFileTransaction(self):
        self.send(path.basename(self.filepath).encode("UTF-8"))
        logging.debug(f"Client sent filename \"{path.basename(self.filepath)}\"")

        self.send(path.getsize(self.filepath))
        logging.debug(f"Client sent filesize \"{path.getsize(self.filepath)} byte(s)\"")

        with open(self.filepath, "rb") as f:
            file = f.read()
            logging.debug(f"Client started sending file...")
            self.send(file)
            logging.debug(f"Client finished transaction!")

        status_b = self.receive()
        isTransactionSuccessful = bool.from_bytes(status_b, "big")
        if isTransactionSuccessful:
            logging.info("Transaction successful.")
        else:
            logging.info("Transaction incomplete.")

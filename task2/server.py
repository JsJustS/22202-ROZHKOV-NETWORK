import socket
import threading
import network
import logging
from os import path, makedirs
import time


logging.basicConfig(
    format="%(levelname)s: [%(threadName)s] > %(message)s",
    level=logging.DEBUG
)


class Server(network.App):
    PATH = "uploads"

    def __init__(self, port: int, max_clients_simultaneously=5):
        super().__init__("0.0.0.0", port)
        self.max_clients_amount = max_clients_simultaneously

        self.accepting_thread = None
        self.__worker_idx = 0

    @staticmethod
    def ensureDirectoryExists():
        files_dir = path.join(path.curdir, Server.PATH)
        makedirs(files_dir, exist_ok=True)

    def start(self) -> None:
        super().start()

        self._socket.bind((self.host, self.port))
        self._socket.listen(self.max_clients_amount)

        self.accepting_thread = AcceptingThread(self)
        self.accepting_thread.start()

    def accept(self) -> tuple:
        return self._socket.accept()

    def getWorkerIdx(self):
        n = self.__worker_idx
        self.__worker_idx += 1
        return n


class AcceptingThread(threading.Thread):
    def __init__(self, server: Server):
        super().__init__(name="accept-thread")
        self.server = server
        self.workers = list()

    def run(self) -> None:
        while self.is_alive():
            connection = self.server.accept()
            cl_host, cl_port = connection[1]
            self.workers.append(WorkerThread(connection[0], cl_host, cl_port, self.server.getWorkerIdx()))
            self.workers[-1].start()


class WorkerThread(threading.Thread):
    def __init__(self, sock: socket.socket, client_host: str, client_port: int, idx: int):
        super().__init__(name="worker-thread-" + str(idx))
        self.socket = sock
        self.host = client_host
        self.port = client_port
        self._idx = idx
        self.timer = None

    def receive(self):
        chunks = []
        last_packet = False
        while not last_packet:
            chunk_len_b = self.socket.recv(network.PacketGenerator.LEN_BYTES)
            if chunk_len_b == b'':
                logging.error("chunk_len_b missing")
                raise RuntimeError("socket connection broken")

            flag_byte = self.socket.recv(1)
            if flag_byte == b'':
                logging.error("flag_byte missing")
                raise RuntimeError("socket connection broken")
            last_packet = False if flag_byte == b'\x00' else True

            chunk_len = int.from_bytes(chunk_len_b, "big")
            chunk = self.socket.recv(chunk_len)
            if chunk == b'':
                logging.error("chunk missing")
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)

            if self.timer is not None:
                self.timer.update(time.time_ns(), network.PacketGenerator.LEN_BYTES + 1 + chunk_len)
        return b''.join(chunks)

    def run(self) -> None:
        try:
            self.handleClient()
        except RuntimeError as e:
            self.socket.close()
            self.timer.stop()
            logging.error(f"Socket connection was broken! " + str(e))

    def handleClient(self):
        Server.ensureDirectoryExists()

        filename = self.receive().decode("UTF-8")
        logging.debug(f"filename: {filename}")

        file_length = int.from_bytes(self.receive(), "big", signed=True)
        logging.debug(f"file_length: {file_length} byte(s)")

        logging.debug(f"started downloading...")
        self.timer = TimeCounterThread(3, num=self._idx)
        self.timer.start()
        self.timer.update(time.time_ns(), 0)

        file_bytes = self.receive()
        files_dir = path.join(path.curdir, Server.PATH)
        with open(path.join(files_dir, filename), "wb") as f:
            f.write(file_bytes)

        self.timer.stop()
        logging.debug(f"finished downloading {filename}! Check {path.join(Server.PATH, filename)}.")

        if path.getsize(path.join(files_dir, filename)) == file_length:
            logging.info("Transaction successful.")
            self.socket.send(bytes(network.PacketGenerator(True)))
        else:
            logging.info("Transaction incomplete.")
            self.socket.send(bytes(network.PacketGenerator(False)))


class TimeCounterThread(threading.Thread):
    def __init__(self, interval: float, num=None):
        super().__init__(
            name=("Timer" if num is None else f"Timer-{num}")
        )
        self.interval = interval
        self._event = threading.Event()

        self.first_unix = None
        self.total_bytes_recv = 0

        self.last_bytes_recv = 0

    def run(self):
        while not self._event.wait(self.interval):
            self.log()
        self.log(total=True)

    def update(self, unix: int, bytes_recv: int):
        self.last_bytes_recv = bytes_recv
        self.total_bytes_recv += bytes_recv
        if self.first_unix is None:
            self.first_unix = unix

    def log(self, total=False):
        if self.first_unix is None:
            return
        current_ns = time.time_ns()
        average = self.total_bytes_recv * 10e9 / (current_ns - self.first_unix)
        cur = self.last_bytes_recv / 3
        if total:
            logging.info(f"average speed: {average:.2f} bytes/sec")
        else:
            logging.info(f"current speed: {cur:.2f} bytes/sec | average speed: {average:.2f} bytes/sec")

    def stop(self):
        self._event.set()

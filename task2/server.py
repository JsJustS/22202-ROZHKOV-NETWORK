import socket
import threading
import network
import logging
from os import path, makedirs


logging.basicConfig(level=logging.DEBUG)


class Server(network.App):
    PATH = "task2\\files"

    def __init__(self, port: int):
        super().__init__("0.0.0.0", port)
        self.max_clients_amount = 5

        self.accepting_thread = None
        self.__worker_idx = 0

    def start(self) -> None:
        super().start()

        files_dir = path.join(path.curdir, Server.PATH)
        makedirs(files_dir, exist_ok=True)

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
        print(*chunks, sep="\n")
        return b''.join(chunks)

    def run(self) -> None:
        try:
            self.handleClient()
        except RuntimeError as e:
            logging.error(f"[{self.name}] Socket connection was broken!")

    def handleClient(self):
        filename = self.receive().decode("UTF-8")
        logging.debug(f"[{threading.currentThread().getName()}] filename: {filename}")

        file_length = int.from_bytes(self.receive(), "big", signed=True)
        logging.debug(f"[{threading.currentThread().getName()}] file_length: {file_length}")

        logging.debug(f"[{threading.currentThread().getName()}] started downloading...")
        file_bytes = self.receive()
        #  print(file_bytes)

        files_dir = path.join(path.curdir, Server.PATH)

        with open(path.join(files_dir, filename), "wb") as f:
            f.write(file_bytes)
        logging.debug(f"[{threading.currentThread().getName()}] finished downloading {filename}! Check {path.join(Server.PATH, filename)}.")

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
        chunk_len_b = self.socket.recv(network.PacketGenerator.LEN_BYTES)
        if chunk_len_b == b'':
            logging.error("chunk_len_b missing")
            raise Exception("socket connection broken")

        flag_byte = self.socket.recv(1)
        if flag_byte == b'':
            logging.error("flag_byte missing")
            raise Exception("socket connection broken")
        last_packet = False if flag_byte == b'\x00' else True

        chunk_len = int.from_bytes(chunk_len_b, "big")
        chunk = self.socket.recv(chunk_len)
        if len(chunk) < chunk_len:
            logging.error("chunk missing")
            raise Exception("socket connection broken")
        return chunk, last_packet

    def receivePacket(self):
        chunks = []
        last_packet = False
        while not last_packet:
            chunk, last_packet = self.receive()
            chunks.append(chunk)

            if self.timer is not None:
                self.timer.update(time.time_ns(), network.PacketGenerator.LEN_BYTES + 1 + len(chunk))
        return b''.join(chunks)

    def receiveFile(self, file):
        last_packet = False
        while not last_packet:
            chunk, last_packet = self.receive()

            file.write(chunk)

            if self.timer is not None:
                self.timer.update(time.time_ns(), len(chunk))

    def run(self) -> None:
        try:
            self.handleClient()
        except Exception as e:
            self.socket.close()
            self.timer.stop()
            logging.error(f"Socket connection was broken! " + str(e))

    def handleClient(self):
        Server.ensureDirectoryExists()

        filename = self.receivePacket().decode("UTF-8")
        logging.debug(f"filename: {filename}")

        file_length = int.from_bytes(self.receivePacket(), "big", signed=True)
        logging.debug(f"file_length: {file_length} byte(s)")

        logging.debug(f"started downloading...")
        self.timer = TimeCounterThread(3, num=self._idx, file_size=file_length)
        self.timer.start()
        self.timer.update(time.time_ns(), 0)

        files_dir = path.join(path.curdir, Server.PATH)

        f = open(path.join(files_dir, filename), mode="wb+")
        try:
            self.receiveFile(f)
        except Exception as e:
            logging.error("could not receive file. " + str(e))
        finally:
            f.close()

        self.timer.stop()
        logging.debug(f"finished downloading {filename}! Check {path.join(Server.PATH, filename)}.")

        if path.getsize(path.join(files_dir, filename)) == file_length:
            logging.info("Transaction successful.")
            self.socket.send(bytes(network.PacketGenerator(True)))
        else:
            logging.info("Transaction incomplete.")
            self.socket.send(bytes(network.PacketGenerator(False)))


class TimeCounterThread(threading.Thread):
    def __init__(self, interval: float, num=None, file_size=None):
        super().__init__(
            name=("Timer" if num is None else f"Timer-{num}")
        )
        self.file_size = file_size

        self.interval = interval
        self._event = threading.Event()
        self._lock = threading.Lock()

        self.first_ns = None
        self.total_bytes_recv = 0

        self.since_last_log = 0

    def run(self):
        while not self._event.wait(self.interval):
            self.log()
        self.log(total=True)

    def update(self, ns: int, bytes_recv: int):
        self._lock.acquire()

        self.since_last_log += bytes_recv
        self.total_bytes_recv += bytes_recv
        if self.first_ns is None:
            self.first_ns = ns

        self._lock.release()

    def log(self, total=False):
        self._lock.acquire()
        if self.first_ns is None:
            return
        first_ns, total_bytes_recv, since_last_log = self.first_ns, self.total_bytes_recv, self.since_last_log
        self._lock.release()

        current_ns = time.time_ns()
        average = total_bytes_recv * 1e9 / min(1, (current_ns - first_ns))
        cur = since_last_log / self.interval
        self._lock.acquire()
        self.since_last_log = 0
        self._lock.release()

        msg = f"average speed: {average:.2f} bytes/sec"
        if not total:
            msg = f"current speed: {cur:.2f} bytes/sec | " + msg
            if self.file_size is not None and self.file_size > 0:
                msg = msg + f" | progress: {100 * total_bytes_recv / self.file_size:.2f}%"

        logging.info(msg)

    def stop(self):
        self._event.set()

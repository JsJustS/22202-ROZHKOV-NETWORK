import threading
import uuid
import socket
import argparse
from typing import Optional, Union


class PacketGenerator:
    LEN_BYTES = 4

    def __init__(
            self,
            abstract_data,
            length=1024,
            encoding="UTF-8"
    ):
        self.abstract_data = abstract_data
        self.packet_piece_length_part_bytes = length
        self._encoding = encoding

    def __bytes__(self):
        if isinstance(self.abstract_data, str):
            abstract_bytes = bytes(self.abstract_data, self._encoding)
        elif isinstance(self.abstract_data, int):
            abstract_bytes = int(self.abstract_data).to_bytes(7, "big", signed=True)
        elif isinstance(self.abstract_data, bool):
            abstract_bytes = bool.to_bytes(self.abstract_data, 1, "big")
        else:  # something custom
            abstract_bytes = bytes(self.abstract_data)

        bytes_string = b''
        while abstract_bytes:
            bytes_left = len(abstract_bytes)

            piece_len = min(self.packet_piece_length_part_bytes, bytes_left)

            bytes_string += int(piece_len).to_bytes(PacketGenerator.LEN_BYTES, "big")
            bytes_string += b'\x00' if bytes_left > self.packet_piece_length_part_bytes else b'\x01'
            bytes_string += abstract_bytes[:piece_len]
            abstract_bytes = abstract_bytes[piece_len:]
        return bytes_string


class App:
    def __init__(self, host: str, port: int, reuse_address_opt: bool = True):
        self.host = host
        self.port = port

        self._socket_reuse_address = reuse_address_opt
        data = socket.getaddrinfo(self.host, None)[0]
        self._socket_family = data[0]
        self._socket = None

    def _setup_socket(self):
        sock = socket.socket(
            family=self._socket_family,
            type=socket.SOCK_STREAM,  # socket type (stream/datagram)
            proto=socket.IPPROTO_TCP  # protocol
        )

        # http://man.he.net/?topic=setsockopt&section=all
        # Set socket address to be reusable for testing purposes
        sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            self._socket_reuse_address
        )

        return sock

    def start(self) -> None:
        self._socket = self._setup_socket()

    def _send(self, data: bytes) -> None:
        if self._socket is None:
            raise RuntimeError("Trying to send data without establishing socket")
        self._socket.send(data)

    def send(self, data: Union[str, int, bytes]) -> None:
        self._send(bytes(PacketGenerator(data, length=4096)))

    def _receive(self) -> bytes:
        if self._socket is None:
            raise RuntimeError("Trying to receive data without establishing socket")

        chunks = []
        last_packet = False
        while not last_packet:
            chunk_len_b = self._socket.recv(PacketGenerator.LEN_BYTES)
            if chunk_len_b == b'':
                raise RuntimeError("socket connection broken")

            flag_byte = self._socket.recv(1)
            if flag_byte == b'':
                raise RuntimeError("socket connection broken")
            last_packet = False if flag_byte == b'\x00' else True

            chunk_len = int.from_bytes(chunk_len_b, "big")
            chunk = self._socket.recv(chunk_len)
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
        return b''.join(chunks)

    def receive(self) -> bytes:
        return self._receive()

    @property
    def is_ipv4(self):
        return self._socket_family == socket.AF_INET

    def die(self) -> None:
        self._socket.close()
        self._socket = None

    def is_alive(self) -> bool:
        return self._socket is not None


if __name__ == "__main__":
    a = PacketGenerator("HELLO")
    a_bytes = bytes(a)
    print(a_bytes, len(a_bytes), sep="\n")

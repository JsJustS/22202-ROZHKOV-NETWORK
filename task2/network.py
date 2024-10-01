import threading
import uuid
import socket
import argparse
from typing import Optional


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
        if type(self.abstract_data) == str:
            abstract_bytes = bytes(self.abstract_data, self._encoding)
        elif type(self.abstract_data) == int:
            abstract_bytes = int(self.abstract_data).to_bytes(PacketGenerator.LEN_BYTES, "big", signed=True)
        elif type(self.abstract_data) == bytes:
            abstract_bytes = self.abstract_data
        else:
            abstract_bytes = bytes(self.abstract_data)

        bytes_string = b''
        while abstract_bytes:
            bytes_left = len(abstract_bytes)

            if bytes_left > self.packet_piece_length_part_bytes:
                bytes_string += int(self.packet_piece_length_part_bytes).to_bytes(PacketGenerator.LEN_BYTES, "big")
                bytes_string += b'\x00'  # not last
                bytes_string += abstract_bytes[:self.packet_piece_length_part_bytes]
                abstract_bytes = abstract_bytes[self.packet_piece_length_part_bytes:]
            else:
                bytes_string += int(bytes_left).to_bytes(PacketGenerator.LEN_BYTES, "big")
                bytes_string += b'\x01'  # last
                bytes_string += abstract_bytes[:bytes_left]
                abstract_bytes = abstract_bytes[bytes_left:]
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
            RuntimeError("Trying to send data without establishing socket")
        pass

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

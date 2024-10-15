import socket
from enum import Enum
import logging


class HandshakeStep(Enum):
    NOT_CONTACTED = 0
    CLIENT_GREETING = 1
    CLIENT_CONNECTION_REQUEST = 2


class ProxyClient:

    def __init__(self, sock: socket.socket, host: str = None, port: int = None):
        self.is_alive = True
        self.proxy_server_socket = sock
        self.proxy_destination_socket = None
        self.host = host
        self.port = port
        self.handshake_step = HandshakeStep.NOT_CONTACTED

    def serve(self):
        match self.handshake_step:
            case HandshakeStep.NOT_CONTACTED:
                self.handshake_step = HandshakeStep.CLIENT_GREETING
                logging.info(f"{self.host}:{self.port} > set state as GREETING")
            case HandshakeStep.CLIENT_GREETING:
                logging.info(f"{self.host}:{self.port} > Greetings!")
                data = self.proxy_server_socket.recv(1)
                if data != b'\x05':
                    logging.debug(f"{self.host}:{self.port} > Not SOCKS5. Aborting.")
                    self.abort()
                    return
                num = self.proxy_server_socket.recv(1)
                data = bytearray(self.proxy_server_socket.recv(int.from_bytes(num, "big")))
                print(data)
                for i in data:
                    if bytes(i) == b'\x00':
                        self.proxy_server_socket.send(b'\x05\x00')
                        self.handshake_step = HandshakeStep.CLIENT_CONNECTION_REQUEST
                        logging.debug(f"{self.host}:{self.port} > Good, greetings went well. Moving on...")
                        return
                logging.debug(f"{self.host}:{self.port} > No \"No Auth\" option. Aborting.")
                self.proxy_server_socket.send(b'\x05\xFF')
                self.abort()

    def close(self):
        if self.proxy_server_socket is not None:
            self.proxy_server_socket.close()
        if self.proxy_destination_socket is not None:
            self.proxy_destination_socket.close()

    def abort(self):
        self.close()
        self.is_alive = False

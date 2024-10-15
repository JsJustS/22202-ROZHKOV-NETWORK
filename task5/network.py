import socket
from enum import Enum
import logging


class HandshakeStep(Enum):
    NOT_CONTACTED = 0
    CLIENT_GREETING = 1
    CLIENT_CONNECTION_REQUEST = 2
    CLIENT_ACTIVE = 3


class ProxyClient:

    def __init__(self, sock: socket.socket, host: str = None, port: int = None):
        self.is_alive = True
        self.proxy_server_socket = sock
        self.proxy_destination_socket = None
        self.host = host
        self.port = port
        self.handshake_step = HandshakeStep.NOT_CONTACTED

    def serve(self):
        if not self.is_alive:
            return
        match self.handshake_step:
            case HandshakeStep.NOT_CONTACTED:
                self.handshake_step = HandshakeStep.CLIENT_GREETING
                logging.info(f"{self.host}:{self.port} > set state as GREETING")
            case HandshakeStep.CLIENT_GREETING:
                logging.info(f"{self.host}:{self.port} > Greetings!")
                data = self.proxy_server_socket.recv(1)
                if bytes(data) != b'\x05':
                    logging.debug(f"{self.host}:{self.port} > Not SOCKS5. Aborting.")
                    self.abort()
                    return
                num = self.proxy_server_socket.recv(1)
                data = self.proxy_server_socket.recv(int.from_bytes(num, "big"))

                if b'\x00' in data:
                    self.proxy_server_socket.send(b'\x05\x00')
                    self.handshake_step = HandshakeStep.CLIENT_CONNECTION_REQUEST
                    logging.debug(f"{self.host}:{self.port} > Good, greetings went well. Moving on...")
                    return
                logging.debug(f"{self.host}:{self.port} > No \"No Auth\" option. Aborting.")
                self.proxy_server_socket.send(b'\x05\xFF')
                self.abort()
            case HandshakeStep.CLIENT_CONNECTION_REQUEST:
                logging.info(f"{self.host}:{self.port} > Client requests connection...")
                data = self.proxy_server_socket.recv(1)
                if bytes(data) != b'\x05':
                    logging.debug(f"{self.host}:{self.port} > Not SOCKS5. Aborting.")
                    self.abort()
                    return
                cmd = self.proxy_server_socket.recv(1)
                if bytes(cmd) != b'\x01':
                    logging.debug(f"{self.host}:{self.port} > command is not supported.")
                    self.proxy_server_socket.send(b'\x05\x07\x00\x03\x00\x00\x00')
                    self.abort()
                    return
                self.proxy_server_socket.recv(1)  # reserved \x00
                address_type = self.proxy_server_socket.recv(1)
                address = None
                logging.debug(f"{self.host}:{self.port} > address type {address_type}.")
                match address_type:
                    case b'\x01':
                        ipv4 = self.proxy_server_socket.recv(4)
                        address = socket.inet_ntop(socket.AF_INET, ipv4)
                        logging.debug(f"{self.host}:{self.port} > address ipv4 {address}.")
                    case b'\x03':
                        length = self.proxy_server_socket.recv(1)
                        domain = self.proxy_server_socket.recv(int.from_bytes(length, "big"))
                        address = socket.gethostbyname(domain.decode("utf-8"))
                        logging.debug(f"{self.host}:{self.port} > address from dns {address}, {domain} of length {int.from_bytes(length, 'big')}.")
                    case b'\x04':
                        ipv6 = self.proxy_server_socket.recv(16)
                        address = socket.inet_ntop(socket.AF_INET6, ipv6)
                        logging.debug(f"{self.host}:{self.port} > address ipv6 {address}.")
                    case _:
                        logging.debug(f"{self.host}:{self.port} > address is not supported.")
                        self.proxy_server_socket.send(b'\x05\x07\x00\x03\x00\x00\x00')
                        self.abort()
                        return
                port_b = self.proxy_server_socket.recv(2)
                port = int.from_bytes(port_b, "big")

                # Parsed packet
                if self.open_destination_connection(address, port):
                    self.proxy_server_socket.send(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
                    self.handshake_step = HandshakeStep.CLIENT_ACTIVE
                    return
                self.proxy_server_socket.send(b'\x05\x01\x00\x01\x00\x00\x00\x00\x00\x00')
                self.abort()
            case HandshakeStep.CLIENT_ACTIVE:
                data = self.proxy_server_socket.recv(4096)
                logging.debug(f"{self.host}:{self.port} >>> {data}")
                if len(data) == 0:
                    self.abort()
                    return
                self.proxy_destination_socket.send(data)

    def resend(self):
        if not self.is_alive:
            return
        data = self.proxy_destination_socket.recv(4096)
        logging.debug(f"{self.host}:{self.port} <<< {data}")
        self.proxy_server_socket.send(data)
        if len(data) == 0:
            self.abort()

    def open_destination_connection(self, host: str, port: int) -> bool:
        try:
            self.proxy_destination_socket = socket.socket(
                family=socket.AF_INET,
                type=socket.SOCK_STREAM,  # socket type (stream/datagram)
                proto=socket.IPPROTO_TCP  # protocol
            )

            # http://man.he.net/?topic=setsockopt&section=all
            # Set socket address to be reusable for testing purposes
            self.proxy_destination_socket.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1
            )

            self.proxy_destination_socket.setblocking(False)
            self.proxy_destination_socket.settimeout(60)
            self.proxy_destination_socket.connect((host, port))
        except Exception as e:
            logging.error(f"Could not open destination socket due to an error {e}")
            return False
        return True

    def close(self):
        if self.proxy_server_socket is not None:
            self.proxy_server_socket.close()
        if self.proxy_destination_socket is not None:
            self.proxy_destination_socket.close()

    def abort(self):
        self.close()
        self.is_alive = False

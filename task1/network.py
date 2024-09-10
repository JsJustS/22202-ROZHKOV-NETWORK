import threading
import uuid
import socket
import argparse
from typing import Optional


class Packet:

    def __init__(self, program_uuid: uuid.UUID = None, secret: str = None, alive: bool = True, from_bytes: bytes = None):
        if from_bytes is None:
            self.uuid = program_uuid
            self.alive = alive
            self.secret = secret
            return
        if len(from_bytes) < 17:
            raise RuntimeError("Tried to generate packet with not enough bytes")

        self.alive = bool(from_bytes[-1])
        self.uuid = uuid.UUID(bytes=from_bytes[-17:-1])
        self.secret = from_bytes[:-17].decode("ascii")

    def __bytes__(self):
        return bytes(self.secret, "ascii") + self.uuid.bytes + (b'\x01' if self.alive else b'\x00')

    @property
    def bytes(self) -> bytes:
        return bytes(self)

    def __len__(self) -> int:
        return len(self.secret) + len(self.uuid.bytes) + 1

    def __str__(self):
        return f"Packet[secret=\"{self.secret}\", uuid={self.uuid}, alive={self.alive}]"


class App(threading.Timer):
    def __init__(self, secret="default-secret", ttl: int = 1, reuse_address_opt: bool = True,
                 loop_message_opt: bool = True):
        super().__init__(0, lambda: None)
        self.secret = secret

        args = App.__parse()
        self.secret = secret if args.secret is None else args.secret
        self.multicast_group = args.group
        self.multicast_port = args.port
        self.multicast_ttl = ttl
        self.delay = args.delay
        self.delay_modifier = 1.2

        self.uuid = uuid.uuid4()

        self._socket_reuse_address = reuse_address_opt
        self._socket_loop_message = loop_message_opt
        data = socket.getaddrinfo(self.multicast_group, None)[0]
        self._socket_family = data[0]
        self._socket = None

    def _setup_socket(self):
        sock = socket.socket(
            family=self._socket_family,
            type=socket.SOCK_DGRAM,  # socket type (stream/datagram)
            proto=socket.IPPROTO_UDP  # protocol
        )

        # http://man.he.net/?topic=setsockopt&section=all
        # Set socket address to be reusable for testing purposes
        sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            self._socket_reuse_address
        )

        sock.setsockopt(
            socket.IPPROTO_IP if self.is_ipv4 else socket.IPPROTO_IPV6,
            socket.IP_MULTICAST_LOOP if self.is_ipv4 else socket.IPV6_MULTICAST_LOOP,
            self._socket_loop_message
        )

        sock.setsockopt(
            socket.IPPROTO_IP if self.is_ipv4 else socket.IPPROTO_IPV6,
            socket.IP_MULTICAST_TTL if self.is_ipv4 else socket.IPV6_MULTICAST_HOPS,
            self.multicast_ttl
        )

        if self.is_ipv4:
            intf = socket.gethostbyname(socket.gethostname())
            sock.setsockopt(
                socket.IPPROTO_IP if self.is_ipv4 else socket.IPPROTO_IPV6,
                socket.IP_MULTICAST_IF if self.is_ipv4 else socket.IPV6_MULTICAST_IF,
                socket.inet_aton(intf)
            )

        sock.bind(self.bind_address)

        # adding to multicast group, enables us to receive multicast datagrams
        mreq = socket.inet_pton(self._socket_family, self.multicast_group) + socket.inet_aton('0.0.0.0')
        sock.setsockopt(
            socket.IPPROTO_IP if self.is_ipv4 else socket.IPPROTO_IPV6,
            socket.IP_ADD_MEMBERSHIP if self.is_ipv4 else socket.IPV6_JOIN_GROUP,
            mreq
        )

        return sock

    def start(self) -> None:
        self._socket = self._setup_socket()
        super().start()

    def run(self):
        self.send_packet(
            Packet(
                program_uuid=self.uuid,
                secret=self.secret,
            )
        )
        while not self.finished.wait(self.delay):
            self.send_packet(
                Packet(
                    program_uuid=self.uuid,
                    secret=self.secret,
                )
            )

    def send_packet(self, packet: Packet) -> None:
        self._send(packet.bytes)

    def _send(self, data: bytes) -> None:
        if self._socket is None:
            RuntimeError("Trying to send data without establishing socket")
        self._socket.sendto(data, self.multicast_address)

    @property
    def expected_packet_len(self):
        return len(self.secret) + len(self.uuid.bytes) + 1

    @property
    def is_ipv4(self):
        return self._socket_family == socket.AF_INET

    def receive_packet(self) -> Optional[Packet]:
        internal_damage_counter = 5
        if self._socket is None:
            return None
        packet = None
        while packet is None:
            try:
                received_bytes = self._socket.recv(self.expected_packet_len)
            except OSError:
                internal_damage_counter -= 1
                if internal_damage_counter == 0:
                    return None

            if len(received_bytes) != self.expected_packet_len:
                continue
            packet = Packet(from_bytes=received_bytes)
            if packet.secret != self.secret:
                packet = None
        return packet

    def die(self) -> None:
        self.send_packet(
            Packet(
                program_uuid=self.uuid,
                secret=self.secret,
                alive=False
            )
        )
        self.cancel()
        self._socket.close()

    def is_alive(self) -> bool:
        return self._socket is not None and not self.is_dead()

    def is_dead(self) -> bool:
        return self.finished.is_set()


    @property
    def multicast_address(self):
        return self.multicast_group, self.multicast_port

    @property
    def bind_address(self):
        return "", self.multicast_port

    @staticmethod
    def __parse():
        parser = argparse.ArgumentParser(
            prog="Task 1",
            description="First Task for Networking Sem.5"
        )

        parser.add_argument('-g', '--group', default="239.192.1.100")
        parser.add_argument('-p', '--port', type=int, default=5123)
        parser.add_argument('-d', '--delay', type=int, default=1)
        parser.add_argument('-s', '--secret', default=None)
        return parser.parse_args()

import socket
import snakes.snakes_pb2 as snakes
import time


class NetworkHandler:
    MULTICAST_GROUP = "239.192.0.4"
    MULTICAST_PORT = 9192

    def __init__(self):
        self.multicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.multicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        self.multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        self.multicast_socket.bind(("", NetworkHandler.MULTICAST_GROUP))
        mreq = socket.inet_pton(socket.AF_INET, NetworkHandler.MULTICAST_GROUP) + socket.inet_aton('0.0.0.0')
        self.multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        self.direct_socket = socket.socket()

        self.previous_time = 0



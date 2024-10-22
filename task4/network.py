import socket
import snakes.snakes_pb2 as snakes
import time

from PyQt6.QtNetwork import QUdpSocket, QAbstractSocket, QHostAddress


class Subscriber:

    def notify(self, message: snakes.GameMessage):
        pass


class NetworkHandler:
    MULTICAST_GROUP = "239.192.0.4"
    MULTICAST_PORT = 9192

    def __init__(self):
        self._subscribers = list()
        # self.direct_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # self.direct_socket.bind(("0.0.0.0", 0))

        self.multicast_socket = QUdpSocket()
        self.multicast_socket.setSocketOption(QAbstractSocket.SocketOption.MulticastTtlOption, 32)
        self.multicast_socket.setSocketOption(QAbstractSocket.SocketOption.MulticastLoopbackOption, 1)
        self.multicast_socket.bind(QHostAddress.SpecialAddress.AnyIPv4, self.MULTICAST_PORT)
        self.multicast_socket.joinMulticastGroup(QHostAddress(self.MULTICAST_GROUP))
        self.multicast_socket.readyRead.connect(self.processDatagram)

        print(self.multicast_socket.state())

    def processDatagram(self):
        while self.multicast_socket.hasPendingDatagrams():
            datagram = self.multicast_socket.receiveDatagram()
            raw = bytes(datagram.data())
            message = snakes.GameMessage()
            message.ParseFromString(raw)
            self.notifySubscribers(message)

    def subscribe(self, subscriber: Subscriber):
        self._subscribers.append(subscriber)

    def notifySubscribers(self, message: snakes.GameMessage):
        for subscriber in self._subscribers:
            subscriber.notify(message)

    def multicast(self, message: snakes.GameMessage):
        print("sent", message.SerializeToString())
        self.multicast_socket.writeDatagram(message.SerializeToString(), QHostAddress(self.MULTICAST_GROUP), self.MULTICAST_PORT)

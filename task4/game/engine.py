import logging

import task4.snakes.snakes_pb2 as snakes
from task4.game.player_manager import PlayerManager, Player
from typing import Union, List, Tuple, Iterable, Set

from task4.network import NetworkHandler


class Snake:
    def __init__(self):
        self.player_id = 0
        self.direction = snakes.Direction.UP
        self.state = snakes.GameState.Snake.SnakeState.ALIVE

        self.head_x = 0
        self.head_y = 0
        self.tail = list()

    def toPoints(self) -> List[Tuple[int, int]]:
        points = list()
        old_x, old_y = self.head_x, self.head_y
        points.append((old_x, old_y))
        for x, y in self.tail:
            dx, dy = x - old_x, y - old_y
            points.append((dx, dy))
            old_x, old_y = x, y
        return points

    def fromPoints(self, points: Union[List[Tuple[int, int]], Iterable[snakes.GameState.Coord]]):
        pass

    def asMsg(self):
        return snakes.GameState.Snake(
            player_id=self.player_id,
            points=map(
                lambda point: snakes.GameState.Coord(x=point[0], y=point[1]),
                self.toPoints()
            ),
            head_direction=self.direction,
            state=self.state
        )


class GameEngine:
    def __init__(
            self,
            initial_host: str,
            initial_port: int,
            server_name: str,
            field_width: int,
            field_height: int,
            food_static: int,
            state_delay_ms: int,
            network_handler: NetworkHandler,
            client_id: int,
            client_name: str,
            client_requested_role: snakes.NodeRole
    ):
        self.host = initial_host
        self.port = initial_port
        self.server_name = server_name
        self.field_width = field_width
        self.field_height = field_height
        self.food_static = food_static
        self.state_delay_ms = state_delay_ms
        self.network_handler = network_handler

        self.player_manager = PlayerManager(
            client_player=Player(
                name=client_name,
                id=client_id,
                ip_address=network_handler.host,
                port=network_handler.port,
                role=client_requested_role,
                is_client=True
            )
        )
        self._snakes = set()
        self._food = set()

    def start(self, is_host: bool):
        pass

    def stop(self):
        pass

    def becomeViewer(self):
        pass

    def getSnakes(self) -> Set[Snake]:
        return self._snakes.copy()

    def getFood(self) -> Set[Tuple[int, int]]:
        return self._food.copy()

    def moveClientSnake(self, direction: snakes.Direction) -> None:
        message = snakes.GameMessage(
            msg_seq=self.msg_seq,
            sender_id=self.player.id,
            steer=snakes.GameMessage.SteerMsg(
                direction=direction
            )
        )
        self.messagesWithoutAck[message.msg_seq] = message
        self.unicast(message, self.server.host, self.server.port)
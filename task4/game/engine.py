import logging

import task4.snakes.snakes_pb2 as snakes
from task4.game.player_manager import PlayerManager, Player
from typing import Union, List, Tuple, Iterable


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
    def __init__(self, host: str, port: int, server_name: str, settings: snakes.GameConfig):
        self.host = host
        self.port = port
        self.server_name = server_name
        self.settings = settings

        self.player_manager = PlayerManager(
            client_player=Player(

            )
        )
        self.snakes = set()

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
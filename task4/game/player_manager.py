import logging

import task4.snakes.snakes_pb2 as snakes
from typing import Set, Union


class Player:
    def __init__(self, name: str, id: int, ip_address: str, port: int, role: snakes.NodeRole, score: int):
        self.name = ""
        self.id = 0
        self.ip_address = ""
        self.port = 1111
        self.role = snakes.NodeRole.NORMAL
        self.score = 0

        self.is_client = True
        self.last_socket_message_got = 0
        self.last_socket_message_sent = 0

    def asMsg(self):
        return snakes.GamePlayer(
            name=self.name,
            id=self.id,
            ip_address=self.ip_address,
            port=self.port,
            role=self.role,
            score=self.score
        )


class PlayerManager:
    def __init__(self, client_player: Player):
        self.client_player = client_player

        self._players = set()
        self.addPlayer(client_player)

    def getPlayers(self, fn=lambda x: True) -> Set[Player]:
        return set(filter(fn, self._players))

    def getPlayerByID(self) -> Union[Player, None]:
        players_with_id = self.getPlayers(lambda x: x.id == id)
        if len(players_with_id) == 0:
            return None
        if len(players_with_id) > 1:
            logging.warn(f"More than 1 player have id {id}")
        return players_with_id.pop()

    def getPlayersWithRole(self, role: snakes.NodeRole) -> Set[Player]:
        players_with_role = self.getPlayers(lambda x: x.role == role)
        return players_with_role

    def getMaster(self) -> Union[Player, None]:
        masters = self.getPlayersWithRole(snakes.NodeRole.MASTER)
        if len(masters) == 0:
            return None
        if len(masters) > 1:
            logging.warn("More than 1 player with MASTER role were found.")
        return masters.pop()

    def getDeputy(self) -> Union[Player, None]:
        deputies = self.getPlayersWithRole(snakes.NodeRole.DEPUTY)
        if len(deputies) == 0:
            return None
        if len(deputies) > 1:
            logging.warn("More than 1 player with DEPUTY role were found.")
        return deputies.pop()

    def addPlayer(self, player: Player) -> None:
        self._players.add(player)

    def removePlayerByID(self, id: int) -> None:
        players_with_id = set(filter(lambda x: x.id == id, self._players))
        if len(players_with_id) > 1:
            logging.warn(f"More than 1 player have id {id}")
        self._players.difference_update(players_with_id)
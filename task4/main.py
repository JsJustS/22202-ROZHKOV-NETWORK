import time

from PyQt6.QtNetwork import QNetworkDatagram

import snakes.snakes_pb2 as snakes
from PyQt6.QtWidgets import QApplication, QWidget, QTableWidgetItem
from PyQt6.QtGui import QMovie
import sys
from qtpy import uic
import json
import os
import logging
import random

from settings import ServerSettingsWindow
from network import NetworkHandler, Subscriber
from game import GameWidget, GameServer


class ClientWindow(QWidget, Subscriber):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi('ui/client.ui', self)
        self.snakes_gif_movie = QMovie('ui/snakes.gif')
        self.gameLabel.setMovie(self.snakes_gif_movie)
        self.snakes_gif_movie.start()

        self.setWindowTitle("Snakes | Client")
        self.loadUserConfig()

        self.playerNameLine.editingFinished.connect(self.saveUserConfig)
        self.hostButton.clicked.connect(self.openServerSettingsScreen)
        self.avaliableGamesTable.cellDoubleClicked.connect(self.onServerDoubleClick)

        self.networkHandler = NetworkHandler()
        self.networkHandler.subscribe(self)

        self.games = dict()
        self.trying_to_join = None

        self.show()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        self.adjustTableSize()

    def joinServer(self, host: str, port: int, game: snakes.GameAnnouncement, player: bool = True):
        message = snakes.GameMessage()
        message.msg_seq = 0
        message.join.player_name = self.playerNameLine.text()
        message.join.game_name = game.game_name
        message.join.requested_role = snakes.NodeRole.NORMAL if player else snakes.NodeRole.VIEWER
        self.networkHandler.unicast(message, host, port)

    def onServerDoubleClick(self, row, col):
        name = self.avaliableGamesTable.item(row, 0).text()
        data = self.games[name]
        self.trying_to_join = name
        self.joinServer(data["host"], data["port"], data["game"])

    def adjustTableSize(self):
        # todo: update player count
        width = self.avaliableGamesTable.width()
        self.avaliableGamesTable.setColumnWidth(0, int(width / 100 * 40) - 1)
        self.avaliableGamesTable.setColumnWidth(1, int(width / 100 * 20) - 1)
        self.avaliableGamesTable.setColumnWidth(2, int(width / 100 * 20) - 1)
        self.avaliableGamesTable.setColumnWidth(3, int(width / 100 * 20))

        # self.avaliableGamesTable.clearContents()
        # self.avaliableGamesTable.setRowCount(0)
        try:
            name_to_row = dict()
            for row in range(self.avaliableGamesTable.rowCount()):
                name_to_row[self.avaliableGamesTable.item(row, 0).text()] = row

            current_time = time.time_ns()
            to_be_deleted = []
            for master, data in self.games.items():
                if current_time - data["last_update"] > 3e9:
                    to_be_deleted.append(master)
                    continue

                if master in name_to_row.keys():
                    continue
                else:
                    row = self.avaliableGamesTable.rowCount()
                    self.avaliableGamesTable.setRowCount(row + 1)

                players = f'{len(data["game"].players.players)}'
                size = f'{data["game"].config.width}x{data["game"].config.height}'
                food = f'{data["game"].config.food_static} + 1x'
                self.avaliableGamesTable.setItem(row, 0, QTableWidgetItem(master))
                self.avaliableGamesTable.setItem(row, 1, QTableWidgetItem(players))
                self.avaliableGamesTable.setItem(row, 2, QTableWidgetItem(size))
                self.avaliableGamesTable.setItem(row, 3, QTableWidgetItem(food))
            for i in to_be_deleted:
                self.games.pop(i)
                self.avaliableGamesTable.removeRow(name_to_row[i])
        except Exception as e:
            print("adjustTableSize", e, type(e))

    def notify(self, datagram: QNetworkDatagram):
        try:
            raw = bytes(datagram.data())
            message = snakes.GameMessage()
            message.ParseFromString(raw)
            match message.WhichOneof("Type"):
                case "announcement":
                    games = message.announcement.games
                    for game in games:
                        if not game.can_join:
                            continue
                        master = list(filter(lambda x: x.role == snakes.NodeRole.MASTER, game.players.players))[0]
                        self.games[master.name] = {
                            "host": datagram.senderAddress(),
                            "port": master.port,
                            "game": game,
                            "last_update": time.time_ns()
                        }
                case "ack":
                    my_id = message.receiver_id
                    self.startGame(my_id)
                case "error":
                    logging.error(message.error.error_message)
        except Exception as e:
            print("notify", e)

    def startGame(self, my_id: int):
        try:
            if self.trying_to_join is None:
                return
            game = self.games[self.trying_to_join]["game"]
            print("my_id", my_id)
            gameWindow = GameWidget(
                self,
                GameServer(
                    self.games[self.trying_to_join]["host"],
                    self.games[self.trying_to_join]["port"],
                    game.game_name,
                    snakes.GameConfig(
                        width=game.config.width,
                        height=game.config.height,
                        food_static=game.config.food_static,
                        state_delay_ms=game.config.state_delay_ms
                    )
                ),
                self.networkHandler,
                my_id
            )

            self.hide()
        except Exception as e:
            print("startGame_main", e)

    def loadUserConfig(self):
        if not os.path.exists("user_conf.json"):
            self.applyBaseConfig()
            self.saveUserConfig()
            return

        try:
            with open("user_conf.json", "r") as js_file:
                conf = json.load(js_file)
                self.playerNameLine.setText(conf["playername"])
        except Exception as e:
            logging.debug(f"Exception while parsing user_conf: {e}")
            self.applyBaseConfig()
            self.saveUserConfig()

    def applyBaseConfig(self):
        self.playerNameLine.setText(f"Player-{random.randint(1, 16677)}")

    def saveUserConfig(self):
        conf = dict()
        if os.path.exists("user_conf.json"):
            with open("user_conf.json", "r") as js_file:
                conf = json.load(js_file)

        conf["playername"] = self.playerNameLine.text()

        with open("user_conf.json", "w") as js_file:
            json.dump(conf, js_file, indent=4)

    def openServerSettingsScreen(self):
        try:
            settingsWindow = ServerSettingsWindow(self)
            self.playerNameLine.setEnabled(False)
            self.hostButton.setEnabled(False)
            self.avaliableGamesTable.setEnabled(False)
        except Exception as e:
            logging.info(e)


if __name__ == "__main__":
    logging.basicConfig(
        format="[%(levelname)s]: %(message)s",
        level=logging.INFO
    )

    app = QApplication(sys.argv)
    clientWindow = ClientWindow()
    app.exec()

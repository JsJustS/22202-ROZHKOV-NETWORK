import snakes.snakes_pb2 as snakes
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QMovie
import sys
from qtpy import uic
import json
import os
import logging
import random

from settings import ServerSettingsWindow
from network import NetworkHandler, Subscriber


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

        self.networkHandler = NetworkHandler()
        self.networkHandler.subscribe(self)

        self.show()

    def notify(self, message: snakes.GameMessage):
        print(message)

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

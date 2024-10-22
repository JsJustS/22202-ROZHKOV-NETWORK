from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QCloseEvent
from qtpy import uic
import os
import json
import logging
import game
import snakes.snakes_pb2 as snakes


class ServerSettingsWindow(QWidget):
    def __init__(self, parent_client: QWidget):
        super().__init__()
        self.client = parent_client
        self.ui = uic.loadUi('ui/config.ui', self)

        self.startButton.clicked.connect(self.startGame)
        self.serverNameLine.editingFinished.connect(self.saveSettings)
        self.widthBox.valueChanged.connect(self.saveSettings)
        self.heightBox.valueChanged.connect(self.saveSettings)
        self.foodBox.valueChanged.connect(self.saveSettings)
        self.delayBox.valueChanged.connect(self.saveSettings)

        self.setWindowTitle("Snakes | Server Settings")
        self.loadSettings()
        self.show()

    def loadSettings(self):
        if not os.path.exists("user_conf.json"):
            self.applyBaseSettings()
            self.saveSettings()
            return

        try:
            with open("user_conf.json", "r") as js_file:
                conf = json.load(js_file)["server"]

                self.serverNameLine.setText(conf["name"])
                self.widthBox.setValue(max(self.widthBox.minimum(), min(self.widthBox.maximum(), conf["width"])))
                self.heightBox.setValue(max(self.heightBox.minimum(), min(self.heightBox.maximum(), conf["height"])))
                self.foodBox.setValue(max(self.foodBox.minimum(), min(self.foodBox.maximum(), conf["food"])))
                self.delayBox.setValue(max(self.delayBox.minimum(), min(self.delayBox.maximum(), conf["delay"])))
        except Exception as e:
            logging.debug(f"Exception while parsing user_conf: {e}")
            self.applyBaseSettings()
            self.saveSettings()

    def applyBaseSettings(self):
        self.serverNameLine.setText(self.client.playerNameLine.text() + "'s game")

        self.widthBox.setValue(40)
        self.heightBox.setValue(30)
        self.foodBox.setValue(1)
        self.delayBox.setValue(1000)

    def saveSettings(self):
        conf = dict()
        if os.path.exists("user_conf.json"):
            with open("user_conf.json", "r") as js_file:
                conf = json.load(js_file)

        server = dict()
        if "server" in conf.keys():
            server = conf["server"]

        server["name"] = self.serverNameLine.text()
        server["width"] = self.widthBox.value()
        server["height"] = self.heightBox.value()
        server["food"] = self.foodBox.value()
        server["delay"] = self.delayBox.value()

        conf["server"] = server

        with open("user_conf.json", "w") as js_file:
            json.dump(conf, js_file, indent=4)

    def startGame(self):
        try:
            gameWindow = game.GameWidget(
                self.client,
                self.serverNameLine.text(),
                snakes.GameConfig(
                    width=self.widthBox.value(),
                    height=self.heightBox.value(),
                    food_static=self.foodBox.value(),
                    state_delay_ms=self.delayBox.value()
                ),
                self.client.networkHandler
            )

            self.hide()
            self.client.hide()
        except Exception as e:
            print(e)

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.client.playerNameLine.setEnabled(True)
        self.client.hostButton.setEnabled(True)
        self.client.avaliableGamesTable.setEnabled(True)

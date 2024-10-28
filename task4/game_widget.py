from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QKeyEvent, QPainter, QColor
from PyQt6.QtWidgets import QWidget, QListWidgetItem

from network import NetworkHandler
from game.engine import GameEngine, Snake
import task4.snakes.snakes_pb2 as snakes
from typing import Set


class GameWidget(QWidget):
    key_pressed = pyqtSignal(QKeyEvent)
    keys_to_directions = {
        16777234: snakes.Direction.LEFT,
        16777235: snakes.Direction.UP,
        16777236: snakes.Direction.RIGHT,
        16777237: snakes.Direction.DOWN
    }

    def __init__(self, client: QWidget, network_handler: NetworkHandler, client_id: int = 0):
        super().__init__()
        self.ui = uic.loadUi('ui/game.ui', self)

        self.engine = GameEngine()
        self.field_widget = FieldWidget()

        self.key_pressed.connect(self.onKey)

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)
        self.key_pressed.emit(event)

    def onKey(self, event: QKeyEvent):
        if event.key() not in self.keys_to_directions.keys():
            return

        self.engine.moveClientSnake(
            self.keys_to_directions[event.key()]
        )

    def paintEvent(self, event) -> None:
        try:
            self.field_widget.draw()

            master = self.engine.player_manager.getMaster()
            if master is not None:
                self.masterLabel.setText(f"MASTER: {master.name}")

            self.foodLabel.setText(f"FOOD: {self.engine.settings.food_static} + {self.engine.player_manager.getPlayers()}")

            self.ratingList.clear()

            sorted_active_players = sorted(
                self.engine.player_manager.getPlayers(
                    lambda x: x.role != snakes.NodeRole.VIEWER
                ),
                key=lambda x: x.player.score,
                reverse=True
            )
            for player in sorted_active_players:
                self.ratingList.addItem(QListWidgetItem(f"{player.score:5} | {player.name}"))
        except Exception as e:
            print("paintEvent", e)


class FieldWidget:
    def __init__(self, canvas: QWidget, parent: QWidget, width: int, height: int):
        self.canvas = canvas
        self.parent = parent
        self.width = width
        self.height = height

        self._painter = None

    def start(self):
        if self._painter is not None:
            return

        self._painter = QPainter(self.parent)
        x, y = self.getPos()
        block_dimension = self.getBlockDimension()
        self._painter.fillRect(
            x, y,
            block_dimension * self.settings.width,
            block_dimension * self.settings.height,
            QColor('black')
        )

    def drawSnakes(self, snakes_set: Set[Snake]):
        a, b = self.getPos()
        base = self.getBlockDimension()
        for snake in snakes_set:
            x, y = self.torPos(snake.head_x, snake.head_y)
            self._painter.fillRect(
                a + x * base,
                b + y * base,
                base, base,
                QColor("blue") if snake.player.id == self.client_id else QColor("red")
            )
            for tail_block in snake.tail:
                self._painter.fillRect(
                    a + (tail_block[0] % self.settings.width) * base,
                    b + (tail_block[1] % self.settings.height) * base,
                    base, base,
                    QColor("aqua") if snake.player.id == self.client_id else QColor("pink")
                )
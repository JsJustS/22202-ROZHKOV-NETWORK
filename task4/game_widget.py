import random
from math import ceil
from string import ascii_letters

from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QKeyEvent, QPainter, QColor
from PyQt6.QtWidgets import QWidget, QListWidgetItem

from network import NetworkHandler
from game.engine import GameEngine, Snake
import task4.snakes.snakes_pb2 as snakes
from typing import Set, Tuple


class GameWidget(QWidget):
    key_pressed = pyqtSignal(QKeyEvent)
    keys_to_directions = {
        16777234: snakes.Direction.LEFT,
        16777235: snakes.Direction.UP,
        16777236: snakes.Direction.RIGHT,
        16777237: snakes.Direction.DOWN
    }

    def __init__(
            self,
            client_widget: QWidget,
            network_handler: NetworkHandler,
            host: str,
            port: int,
            server_name: str,
            game_config: snakes.GameConfig,
            client_id: int = 0,
            is_host: bool = False,
    ):
        super().__init__()
        self.ui = uic.loadUi('ui/game.ui', self)
        self.client_widget = client_widget

        client_name = client_widget.playerNameLine.text()
        if len(client_name) == 0:
            client_name = ''.join(random.choices(ascii_letters))

        client_requested_role = snakes.NodeRole.VIEWER
        if self.modeButton.text() == "MODE: NORMAL":
            client_requested_role = snakes.NodeRole.NORMAL

        self.engine = GameEngine(
            initial_host=host,
            initial_port=port,
            server_name=server_name,
            field_width=game_config.width,
            field_height=game_config.height,
            food_static=game_config.food_static,
            state_delay_ms=game_config.state_delay_ms,
            network_handler=network_handler,
            client_id=client_id,
            client_name=client_name,
            client_requested_role=client_requested_role
        )
        self.field_widget = FieldWidget(
            canvas=self.artWidget,
            parent=self,
            width=0,
            height=0
        )

        self.key_pressed.connect(self.onKey)
        self.leaveButton.connect(self.engine.becomeViewer)

        self.setWindowTitle(f"Snakes | {server_name} | {client_name}")
        self.show()

        self.engine.start(is_host)

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)
        self.key_pressed.emit(event)

    def onKey(self, event: QKeyEvent):
        if event.key() not in self.keys_to_directions.keys():
            return

        self.engine.moveClientSnake(
            self.keys_to_directions[event.key()]
        )

    def closeEvent(self, event) -> None:
        self.engine.stop()

        # return to client widget
        self.client_widget.playerNameLine.setEnabled(True)
        self.client_widget.hostButton.setEnabled(True)
        self.client_widget.avaliableGamesTable.setEnabled(True)
        self.client_widget.show()

    def paintEvent(self, event) -> None:
        try:
            self.drawField()
            self.drawServerData()
            self.updateRatingData()
        except Exception as e:
            print("paintEvent", e)

    def drawField(self) -> None:
        self.field_widget.startDrawing()
        self.field_widget.drawFood(self.engine.getFood())
        self.field_widget.drawSnakes(
            self.engine.getSnakes(),
            client_player_id=self.engine.player_manager.client_player.id
        )
        self.field_widget.stopDrawing()

    def drawServerData(self) -> None:
        master = self.engine.player_manager.getMaster()
        if master is not None:
            self.masterLabel.setText(f"MASTER: {master.name}")
        else:
            self.masterLabel.setText(f"MASTER: <NOT FOUND>")

        self.foodLabel.setText(f"FOOD: {self.engine.food_static} + {self.engine.player_manager.getPlayers()}")

        self.sizeLabel.setText(f"SIZE: {self.engine.field_width}x{self.engine.field_height}")

    def updateRatingData(self):
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


class FieldWidget:
    def __init__(self, canvas: QWidget, parent: QWidget, width: int, height: int):
        self.canvas = canvas
        self.parent = parent
        self.width = width
        self.height = height

        self._painter = None

    def getBlockDimension(self):
        max_width_in_pixels = self.canvas.width()
        max_height_in_pixels = self.canvas.height()
        width_in_blocks = self.width
        height_in_blocks = self.height

        w_pixels_per_block = int(max_width_in_pixels / width_in_blocks)
        h_pixels_per_block = int(max_height_in_pixels / height_in_blocks)

        return min(w_pixels_per_block, h_pixels_per_block)

    def getPos(self):
        block_dimension = self.getBlockDimension()

        left_x = ceil((self.canvas.width() - block_dimension * self.width) / 2)
        top_y = ceil((self.canvas.height() - block_dimension * self.height) / 2)
        return left_x + self.canvas.x(), top_y + self.canvas.y()

    def torPos(self, x, y):
        return x % self.width, y % self.height

    def startDrawing(self):
        if self._painter is not None:
            return

        self._painter = QPainter(self.parent)
        x, y = self.getPos()
        block_dimension = self.getBlockDimension()
        self._painter.fillRect(
            x, y,
            block_dimension * self.width,
            block_dimension * self.height,
            QColor('black')
        )

    def drawFood(self, food_set: Set[Tuple[int, int]]) -> None:
        if self._painter is None:
            return
        a, b = self.getPos()
        base = self.getBlockDimension()
        for x, y in food_set:
            self._painter.fillRect(
                a + x * base,
                b + y * base,
                base, base,
                QColor("green")
            )

    def drawSnakes(self, snakes_set: Set[Snake], client_player_id: int) -> None:
        if self._painter is None:
            return
        a, b = self.getPos()
        base = self.getBlockDimension()
        for snake in snakes_set:
            x, y = self.torPos(snake.head_x, snake.head_y)
            self._painter.fillRect(
                a + x * base,
                b + y * base,
                base, base,
                QColor("blue") if snake.player_id == client_player_id else QColor("red")
            )
            for tail_block in snake.tail:
                self._painter.fillRect(
                    a + (tail_block[0] % self.width) * base,
                    b + (tail_block[1] % self.height) * base,
                    base, base,
                    QColor("aqua") if snake.player_id == client_player_id else QColor("pink")
                )

    def stopDrawing(self):
        if self._painter is None:
            return
        self._painter.end()
        self._painter = None

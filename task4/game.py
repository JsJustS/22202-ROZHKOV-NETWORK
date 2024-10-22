from enum import Enum

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QKeyEvent
from qtpy import uic
import snakes.snakes_pb2 as snakes
from math import ceil
import random


class Direction(Enum):
    LEFT = 1
    UP = 2
    RIGHT = 3
    DOWN = 4


class GameWidget(QWidget):
    keyPressed = pyqtSignal(QKeyEvent)

    def __init__(self, client: QWidget, server_name: str, settings: snakes.GameConfig):
        super().__init__()
        self.ui = uic.loadUi('ui/game.ui', self)

        self.server_name = server_name
        self.settings = settings

        self.client = client
        # update later
        self.client_snake = Snake(self.client)

        self.field = FieldWidget(self.artWidget, self, settings, self.client_snake)

        self.leaveButton.clicked.connect(self.returnToClient)
        self.hostButton.clicked.connect(self.openServerSettings)

        self.keyPressed.connect(self.onKey)

        self.show()

    def returnToClient(self):
        self.client.playerNameLine.setEnabled(True)
        self.client.hostButton.setEnabled(True)
        self.client.avaliableGamesTable.setEnabled(True)
        self.client.show()
        self.close()

    def openServerSettings(self):
        self.leaveButton.setEnabled(False)
        self.hostButton.setEnabled(False)
        self.ratingList.setEnabled(False)
        self.gamesList.setEnabled(False)

        # open host widget

    def paintEvent(self, event):
        try:
            self.field.draw()
        except Exception as e:
            print(e)

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)
        self.keyPressed.emit(event)

    def onKey(self, event: QKeyEvent):
        keys = {
            16777234: Direction.LEFT,
            16777235: Direction.UP,
            16777236: Direction.RIGHT,
            16777237: Direction.DOWN
        }

        if event.key() in keys.keys():
            pass  # send steer message and update direction ONLY when receiving own steer message
            self.client_snake.direction = keys[event.key()]
        else:
            if event.key() == 16777251:  # alt
                self.field.spawnFood()
            self.field.tick()


class Snake:

    def __init__(self, player, x: int = 0, y: int = 0, direction: Direction = Direction.UP):
        self.x = x
        self.y = y
        self.player = player
        self.direction = direction

        self.tail = list()
        # Координаты змейки обновляются и приводятся к координатам тора на поле
        match self.direction:
            case Direction.UP:
                self.tail.append((self.x, self.y + 1))
            case Direction.DOWN:
                self.tail.append((self.x, self.y - 1))
            case Direction.LEFT:
                self.tail.append((self.x + 1, self.y))
            case Direction.RIGHT:
                self.tail.append((self.x - 1, self.y))

    def move(self):
        new_x, new_y = self.x, self.y
        match self.direction:
            case Direction.UP:
                new_y -= 1
            case Direction.DOWN:
                new_y += 1
            case Direction.LEFT:
                new_x -= 1
            case Direction.RIGHT:
                new_x += 1
        last = self.tail[-1]
        self.tail = [(self.x, self.y)] + self.tail[:-1]
        self.x, self.y = new_x, new_y
        return last


class FieldWidget:
    def __init__(self, canvas: QWidget, parent: QWidget, settings: snakes.GameConfig, client_snake: Snake):
        self.field = []
        self.canvas = canvas
        self.parent = parent
        self.settings = settings

        self.snakes = [client_snake]
        self.food = set()

    def tick(self):
        try:
            for snake in self.snakes:
                last = snake.move()
                if self.snakeToTorPos(snake) in self.food:
                    self.food.remove(self.snakeToTorPos(snake))
                    snake.tail.append(last)
            self.parent.update()
        except Exception as e:
            print(e)

    def draw(self):
        try:
            painter = QPainter(self.parent)

            x, y = self.getPos()
            block_dimension = self.getBlockDimension()

            painter.fillRect(
                x, y,
                block_dimension * self.settings.width,
                block_dimension * self.settings.height,
                QColor('black')
            )

            self.drawFood(painter)
            self.drawSnakes(painter)

            painter.end()
        except Exception as e:
            print(e)

    def getBlockDimension(self):
        max_width_in_pixels = self.canvas.width()
        max_height_in_pixels = self.canvas.height()
        width_in_blocks = self.settings.width
        height_in_blocks = self.settings.height

        w_pixels_per_block = int(max_width_in_pixels / width_in_blocks)
        h_pixels_per_block = int(max_height_in_pixels / height_in_blocks)

        return min(w_pixels_per_block, h_pixels_per_block)

    def getPos(self):
        block_dimension = self.getBlockDimension()

        left_x = ceil((self.canvas.width() - block_dimension * self.settings.width) / 2)
        top_y = ceil((self.canvas.height() - block_dimension * self.settings.height) / 2)
        return left_x + self.canvas.x(), top_y + self.canvas.y()

    def drawFood(self, painter: QPainter):
        a, b = self.getPos()
        base = self.getBlockDimension()
        for x, y in self.food:
            painter.fillRect(
                a + x * base,
                b + y * base,
                base, base,
                QColor("green")
            )

    def drawSnakes(self, painter: QPainter):
        try:
            a, b = self.getPos()
            base = self.getBlockDimension()
            for snake in self.snakes:
                x, y = self.snakeToTorPos(snake)
                painter.fillRect(
                    a + x * base,
                    b + y * base,
                    base, base,
                    QColor("blue")
                )
                for tail_block in snake.tail:
                    painter.fillRect(
                        a + (tail_block[0] % self.settings.width) * base,
                        b + (tail_block[1] % self.settings.height) * base,
                        base, base,
                        QColor("aqua")
                    )
        except Exception as e:
            print(e)

    def snakeToTorPos(self, snake: Snake):
        return snake.x % self.settings.width, snake.y % self.settings.height

    def spawnFood(self):
        while True:
            x, y = random.randint(0, self.settings.width - 1), random.randint(0, self.settings.height - 1)
            if (x, y) not in self.food:
                self.food.add((x, y))
                return

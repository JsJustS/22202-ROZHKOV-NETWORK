from enum import Enum

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QKeyEvent
from qtpy import uic
import snakes.snakes_pb2 as snakes
from math import ceil
import random
import threading


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


class Snake:

    def __init__(self, player, x: int = 0, y: int = 0, direction: Direction = Direction.UP):
        self.x = x
        self.y = y
        self.player = player
        self.direction = direction
        self.points = 0

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

    def addPoint(self):
        self.points += 1

    def kill(self):
        pass

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
        self.canvas = canvas
        self.parent = parent
        self.settings = settings

        self.client_snake = client_snake
        self.snakes = [client_snake]
        self.food = set()

        # change if not server
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.setSingleShot(False)
        self.timer.start(self.settings.state_delay_ms)

    def tick(self):
        try:
            # Step 1. Food Update
            food_to_be_deleted = set()

            for snake in self.snakes:
                last = snake.move()
                pos = self.snakeToTorPos(snake)
                if pos in self.food:
                    food_to_be_deleted.add(pos)
                    snake.tail.append(last)
                    snake.addPoint()

            self.food.difference_update(food_to_be_deleted)

            # Step 2. Danger Update
            killing_blocks = dict()
            for s in self.snakes:
                pos = (s.x % self.settings.width, s.y % self.settings.height)
                if pos not in killing_blocks.keys():
                    killing_blocks[pos] = list()
                killing_blocks[pos].append(s)
                for block in s.tail:
                    pos = (block[0] % self.settings.width, block[1] % self.settings.height)
                    if pos not in killing_blocks.keys():
                        killing_blocks[pos] = list()
                    killing_blocks[pos].append(s)

            dead_snakes = list()
            for snake in self.snakes:
                pos = self.snakeToTorPos(snake)
                if pos in killing_blocks.keys():
                    killers = killing_blocks[pos]
                    killers.remove(snake)
                    if len(killers) == 0:
                        continue
                    for killer in killers:
                        if killer != snake:
                            killer.addPoint()
                    self.spawnFoodFromSnake(snake)
                    snake.kill()
                    dead_snakes.append(snake)
            for snake in dead_snakes:
                self.snakes.remove(snake)

            # Step 3. Spawn Food.
            if len(self.food) < self.settings.food_static + len(self.snakes):
                occupied_blocks = [i for i in self.food]
                occupied_blocks.extend([self.snakeToTorPos(s) for s in self.snakes])
                for s in self.snakes:
                    occupied_blocks.extend(s.tail)
                while len(self.food) < self.settings.food_static + len(self.snakes):
                    occupied_blocks.append(self.spawnFood(occupied_blocks))
                    if len(occupied_blocks) == self.settings.width * self.settings.height:
                        break  # no free space for food

            self.parent.update()
        except Exception as e:
            print(e)

    def spawnFoodFromSnake(self, snake: Snake):
        snake_blocks = [(s[0] % self.settings.width, s[1] % self.settings.height) for s in snake.tail]
        snake_blocks.append((snake.x % self.settings.width, snake.y % self.settings.height))

        for block in snake_blocks:
            a = random.random()
            if a < 0.5:
                self.food.add(block)

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
                    QColor("blue") if snake == self.client_snake else QColor("red")
                )
                for tail_block in snake.tail:
                    painter.fillRect(
                        a + (tail_block[0] % self.settings.width) * base,
                        b + (tail_block[1] % self.settings.height) * base,
                        base, base,
                        QColor("aqua") if snake == self.client_snake else QColor("pink")
                    )
        except Exception as e:
            print(e)

    def snakeToTorPos(self, snake: Snake):
        return snake.x % self.settings.width, snake.y % self.settings.height

    def spawnFood(self, occupied_blocks: list = None):
        if occupied_blocks is None:
            occupied_blocks = []

        while True:
            x, y = random.randint(0, self.settings.width - 1), random.randint(0, self.settings.height - 1)
            if (x, y) not in occupied_blocks:
                self.food.add((x, y))
                return x, y

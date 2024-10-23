from PyQt6.QtCore import pyqtSignal, QTimer
from PyQt6.QtNetwork import QNetworkDatagram
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QKeyEvent
from qtpy import uic
import snakes.snakes_pb2 as snakes
from math import ceil
import random
from network import NetworkHandler, Subscriber


class GameWidget(QWidget, Subscriber):
    keyPressed = pyqtSignal(QKeyEvent)

    def __init__(self, client: QWidget, server_name: str, settings: snakes.GameConfig, networkHandler: NetworkHandler, client_id: int = 0):
        super().__init__()
        self.ui = uic.loadUi('ui/game.ui', self)

        self.server_name = server_name
        self.setWindowTitle(self.server_name + " | Snakes")
        self.settings = settings
        self.networkHandler = networkHandler
        self.networkHandler.subscribe(self)

        # <host variables>
        self.announcementTimer = None
        self.snake_last_id = 0
        if client_id == 0:
            self.becomeMaster()
        # </host variables>

        self.client = client
        self.player = snakes.GamePlayer(
            name=self.client.playerNameLine.text(),
            id=client_id,  # fix later
            port=self.networkHandler.port,
            role=snakes.NodeRole.MASTER if client_id == 0 else snakes.NodeRole.NORMAL,
            score=0
        )


        # update later
        self.client_snake = Snake(self.player)
        self.snake_last_id += 1

        self.field = FieldWidget(self.artWidget, self, settings, self.client_snake, client_id == 0)

        # self.leaveButton.clicked.connect(self.returnToClient)
        self.hostButton.clicked.connect(self.openServerSettings)

        self.keyPressed.connect(self.onKey)

        self.show()

    def notify(self, datagram: QNetworkDatagram):
        match message.WhichOneof("Type"):
            case "join":
                if self.field.getSpawnPos() is not None:
                    pass
                else:
                    self.networkHandler.unicast()

    def adjustTableSize(self):
        width = self.avaliableGamesTable.width()
        self.avaliableGamesTable.setColumnWidth(0, int(width / 100 * 40) - 1)
        self.avaliableGamesTable.setColumnWidth(1, int(width / 100 * 20) - 1)
        self.avaliableGamesTable.setColumnWidth(2, int(width / 100 * 20) - 1)
        self.avaliableGamesTable.setColumnWidth(3, int(width / 100 * 20))

    def becomeMaster(self):
        try:
            self.announcementTimer = QTimer()
            self.announcementTimer.setSingleShot(False)
            self.announcementTimer.timeout.connect(self.sendAnnouncementMsg)
            self.announcementTimer.start(1000)
        except Exception as e:
            print("becomeMaster", e)

    def stopBeingMaster(self):
        try:
            self.player.role = snakes.NodeRole.VIEWER
            if self.announcementTimer is not None:
                self.announcementTimer.stop()
        except Exception as e:
            print("stopBeingMaster", e)

    def sendAnnouncementMsg(self):
        try:
            message = snakes.GameMessage()
            message.msg_seq = 0
            game = message.announcement.games.add()

            game.game_name = self.server_name

            game.config.width = self.settings.width
            game.config.height = self.settings.width
            game.config.food_static = self.settings.food_static
            game.config.state_delay_ms = self.settings.state_delay_ms

            game.can_join = self.field.getSpaceForNewSnake() is not None

            for snake in self.field.snakes:
                player = game.players.players.add()
                player.name = snake.player.name
                player.id = snake.player.id
                player.ip_address = snake.player.ip_address
                player.port = snake.player.port
                player.role = snake.player.role
                player.type = snake.player.type
                player.score = snake.player.score

            self.networkHandler.multicast(message)
        except Exception as e:
            print("sendAnnouncementMsg", e)

    def closeEvent(self, event):
        self.returnToClient()
        self.stopBeingMaster()
        super().closeEvent(event)

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
            self.adjustTableSize()
        except Exception as e:
            print(e)

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)
        self.keyPressed.emit(event)

    def onKey(self, event: QKeyEvent):
        keys = {
            16777234: snakes.Direction.LEFT,
            16777235: snakes.Direction.UP,
            16777236: snakes.Direction.RIGHT,
            16777237: snakes.Direction.DOWN
        }

        if event.key() in keys.keys():
            pass  # send steer message and update direction ONLY when receiving own steer message
            # Если команда заставляет змейку повернуть в направлении, занятом соседней с головой клеткой
            # (попытка повернуть вспять), то такая команда игнорируется.
            self.client_snake.direction = keys[event.key()]
        else:
            if event.key() == 16777251:  # alt
                self.field.spawnFood()


class Snake:

    def __init__(self, player: snakes.GamePlayer, x: int = 0, y: int = 0, direction: snakes.Direction = snakes.Direction.UP):
        self.x = x
        self.y = y
        self.player = player
        self.direction = direction

        self.tail = list()
        # Координаты змейки обновляются и приводятся к координатам тора на поле
        match self.direction:
            case snakes.Direction.UP:
                self.tail.append((self.x, self.y + 1))
            case snakes.Direction.DOWN:
                self.tail.append((self.x, self.y - 1))
            case snakes.Direction.LEFT:
                self.tail.append((self.x + 1, self.y))
            case snakes.Direction.RIGHT:
                self.tail.append((self.x - 1, self.y))

    def addPoint(self):
        self.player.score += 1

    def kill(self):
        pass  # todo: set player role as VIEWER

    def move(self):
        new_x, new_y = self.x, self.y
        match self.direction:
            case snakes.Direction.UP:
                new_y -= 1
            case snakes.Direction.DOWN:
                new_y += 1
            case snakes.Direction.LEFT:
                new_x -= 1
            case snakes.Direction.RIGHT:
                new_x += 1
        last = self.tail[-1]
        self.tail = [(self.x, self.y)] + self.tail[:-1]
        self.x, self.y = new_x, new_y
        return last


class FieldWidget:
    def __init__(self, canvas: QWidget, parent: QWidget, settings: snakes.GameConfig, client_snake: Snake, is_host: bool):
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
        if is_host:
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
                    killers = [s for s in killing_blocks[pos]]
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

    def getSpaceForNewSnake(self):
        # todo: fix later
        return 0, 0

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

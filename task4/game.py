from PyQt6.QtCore import pyqtSignal, QTimer
from PyQt6.QtNetwork import QNetworkDatagram
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QKeyEvent
from google.protobuf.internal.containers import RepeatedCompositeFieldContainer
from qtpy import uic
import snakes.snakes_pb2 as snakes
from math import ceil
import random
from network import NetworkHandler, Subscriber


class GameServer:
    def __init__(self, host: str, port: int, server_name: str, settings: snakes.GameConfig):
        self.host = host
        self.port = port
        self.server_name = server_name
        self.settings = settings


class Snake:

    def __init__(self, player: snakes.GamePlayer, x: int = 0, y: int = 0,
                 direction: snakes.Direction = snakes.Direction.UP):
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


class GameWidget(QWidget, Subscriber):
    keyPressed = pyqtSignal(QKeyEvent)

    def __init__(self, client: QWidget, server: GameServer, networkHandler: NetworkHandler,
                 client_id: int = 0):
        super().__init__()
        self.ui = uic.loadUi('ui/game.ui', self)
        print("client_id", client_id)

        self.server = server
        self.setWindowTitle(self.server.server_name + " | Snakes")
        self.networkHandler = networkHandler
        self.networkHandler.subscribe(self)

        self.state_order = 0

        self.client = client
        self.player = snakes.GamePlayer(
            name=self.client.playerNameLine.text(),
            id=client_id,
            port=self.networkHandler.port,
            role=snakes.NodeRole.MASTER if client_id == 0 else snakes.NodeRole.NORMAL,
            score=0
        )

        self.field = FieldWidget(self.artWidget, self, self.server.settings, client_id, client_id == 0)

        # <host variables>
        self.announcementTimer = None
        self.players = list()
        self.player_last_id = 0
        if client_id == 0:
            self.becomeMaster()
            joinMsg = snakes.GameMessage(
                msg_seq=0,
                join=snakes.GameMessage.JoinMsg(
                    player_type=snakes.PlayerType.HUMAN,
                    player_name=self.player.name,
                    game_name=self.server.server_name,
                    requested_role=snakes.NodeRole.MASTER
                )
            )
            self.networkHandler.unicast(joinMsg, self.networkHandler.host, self.networkHandler.port)
        # </host variables>

        # self.leaveButton.clicked.connect(self.returnToClient)
        self.hostButton.clicked.connect(self.openServerSettings)

        self.keyPressed.connect(self.onKey)

        self.show()
        self.sizeLabel.setText(f"SIZE: {self.server.settings.width}x{self.server.settings.height}")

    def snakeToKeyPoints(self, snake: Snake):
        points = list()
        old_x, old_y = self.field.snakeToTorPos(snake)
        points.append((old_x, old_y))
        for x, y in snake.tail:
            dx, dy = x - old_x, y - old_y
            points.append((dx, dy))
            old_x, old_y = x, y
        return points

    def keyPointsToSnake(self, points: RepeatedCompositeFieldContainer[snakes.GameState.Coord], snake: Snake):
        old_x, old_y = points[0].x, points[0].y
        snake.x, snake.y = points[0].x, points[0].y
        snake.tail = list()
        for point in points[1:]:
            dx, dy = point.x, point.y
            old_x, old_y = (old_x + dx, old_y + dy)
            snake.tail.append((old_x, old_y))

    def sendGameState(self):

        message = snakes.GameMessage(
            msg_seq=self.state_order,
            state=snakes.GameMessage.StateMsg(
                state=snakes.GameState(
                    state_order=self.state_order,
                    players=snakes.GamePlayers(
                        players=self.players
                    ),
                    foods=[snakes.GameState.Coord(x=x, y=y) for x, y in self.field.food],
                    snakes=[snakes.GameState.Snake(
                        player_id=snake.player.id,
                        head_direction=snake.direction,
                        state=snakes.GameState.Snake.SnakeState.ALIVE,
                        points=[snakes.GameState.Coord(x=x, y=y) for x, y in self.snakeToKeyPoints(snake)]
                    ) for snake in self.field.snakes]
                )
            )
        )

        for player in self.players:
            self.networkHandler.unicast(message, player.ip_address, player.port)
        self.state_order += 1

    def notify(self, datagram: QNetworkDatagram):
        raw = bytes(datagram.data())
        message = snakes.GameMessage()
        message.ParseFromString(raw)
        match message.WhichOneof("Type"):

            # server
            case "join":
                pos = self.field.getPosForNewSnake()
                if pos is not None:
                    answer = snakes.GameMessage(ack=snakes.GameMessage.AckMsg())
                    answer.msg_seq = message.msg_seq + 1
                    answer.receiver_id = self.player_last_id
                    self.networkHandler.unicast(answer, datagram.senderAddress(), datagram.senderPort())
                    player = snakes.GamePlayer(
                            name=message.join.player_name,
                            id=self.player_last_id,
                            ip_address=datagram.senderAddress().toString(),
                            port=datagram.senderPort(),
                            role=snakes.NodeRole.VIEWER if message.join.requested_role == snakes.NodeRole.VIEWER else snakes.NodeRole.NORMAL,
                            type=snakes.PlayerType.HUMAN,
                            score=0
                    )

                    # erm...
                    if len(self.players) == 0:
                        self.player.name = player.name
                        self.player.id = player.id
                        self.player.ip_address = player.ip_address
                        self.player.port = player.port
                        self.player.role = snakes.NodeRole.MASTER
                        self.player.type = player.type
                        self.player.score = player.score
                        player = self.player

                    self.players.append(player)
                    if message.join.requested_role != snakes.NodeRole.VIEWER:
                        self.field.addSnake(pos[0], pos[1], player)
                    self.player_last_id += 1
                else:
                    answer = snakes.GameMessage(error=snakes.GameMessage.ErrorMsg("Could not find space on field."))
                    answer.msg_seq = message.msg_seq + 1
                    self.networkHandler.unicast(answer, datagram.senderAddress(), datagram.senderPort())

            case "steer":
                ss = list(filter(lambda x: x.player.id == message.sender_id, self.field.snakes))
                steer_block = {
                    snakes.Direction.DOWN: snakes.Direction.UP,
                    snakes.Direction.UP: snakes.Direction.DOWN,
                    snakes.Direction.LEFT: snakes.Direction.RIGHT,
                    snakes.Direction.RIGHT: snakes.Direction.LEFT,
                }
                if len(ss) < 1:
                    return
                for s in ss:
                    if steer_block[message.steer.direction] != s.direction:
                        s.direction = message.steer.direction
            case "discover":
                self.sendAnnouncementMsg((datagram.senderAddress(), datagram.senderPort()))

            # client
            case "ack":
                self.player.id = message.receiver_id

            case "state":
                if message.state.state.state_order <= self.state_order:
                    return

                self.field.food = [(c.x, c.y) for c in message.state.state.foods]

                for player in message.state.state.players.players:
                    for old_player in self.players:
                        if player.id == old_player.id:
                            old_player.name = player.name
                            old_player.ip_address = player.ip_address
                            old_player.port = player.port
                            old_player.role = player.role
                            old_player.type = player.type
                            old_player.score = player.score
                            break
                    else:
                        self.players.append(player)

                for snake in message.state.state.snakes:
                    for old_snake in self.field.snakes:
                        if old_snake.player.id == snake.player_id:
                            old_snake.direction = snake.head_direction
                            self.keyPointsToSnake(snake.points, old_snake)
                    else:
                        new_snake = Snake(
                            player=list(filter(lambda x: x.id == snake.player_id, self.players))[0],
                            direction=snake.head_direction
                        )
                        self.keyPointsToSnake(snake.points, new_snake)
                        self.field.snakes.append(new_snake)
                self.update()

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

    def sendAnnouncementMsg(self, address: tuple = None):
        try:
            if len(self.field.snakes) < 1:
                return
            message = snakes.GameMessage()
            message.msg_seq = 0
            game = message.announcement.games.add()

            game.game_name = self.server.server_name

            game.config.width = self.server.settings.width
            game.config.height = self.server.settings.width
            game.config.food_static = self.server.settings.food_static
            game.config.state_delay_ms = self.server.settings.state_delay_ms

            game.can_join = self.field.getPosForNewSnake() is not None

            for snake in self.field.snakes:
                player = game.players.players.add()
                player.name = snake.player.name
                player.id = snake.player.id
                player.ip_address = snake.player.ip_address
                player.port = snake.player.port
                player.role = snake.player.role
                player.type = snake.player.type
                player.score = snake.player.score

            if address is None:
                self.networkHandler.multicast(message)
            else:
                self.networkHandler.unicast(message, address[0], address[1])
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
            self.masterLabel.setText(f"MASTER: {list(filter(lambda x: x.role == snakes.NodeRole.MASTER, self.players))[0].name}")
            self.foodLabel.setText(f"FOOD: {self.server.settings.food_static} + {len(self.field.snakes)}")
        except Exception as e:
            print("paintEvent", e)

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)
        self.keyPressed.emit(event)

    def onKey(self, event: QKeyEvent):
        keys_to_directions = {
            16777234: snakes.Direction.LEFT,
            16777235: snakes.Direction.UP,
            16777236: snakes.Direction.RIGHT,
            16777237: snakes.Direction.DOWN
        }

        if event.key() in keys_to_directions.keys():
            messages = snakes.GameMessage()
            messages.msg_seq = 0
            messages.sender_id = self.player.id
            messages.steer.direction = keys_to_directions[event.key()]
            self.networkHandler.unicast(messages, self.server.host, self.server.port)


class FieldWidget:
    def __init__(self, canvas: QWidget, parent: QWidget, settings: snakes.GameConfig, client_id: int, is_host: bool):
        self.canvas = canvas
        self.parent = parent
        self.settings = settings

        self.snakes = []
        self.food = set()
        self.state_id = 0

        # change if not server
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.setSingleShot(False)

        self.client_id = client_id
        if is_host:
            self.timer.start(self.settings.state_delay_ms)

    def addSnake(self, x: int, y: int, player: snakes.GamePlayer):
        snake = Snake(player, x=x, y=y, direction=random.choice([snakes.Direction.UP, snakes.Direction.DOWN, snakes.Direction.LEFT, snakes.Direction.RIGHT]))
        self.snakes.append(snake)

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
                occupied_blocks = self.getOccupiedBlocks()
                while len(self.food) < self.settings.food_static + len(self.snakes):
                    occupied_blocks.append(self.spawnFood(occupied_blocks))
                    if len(occupied_blocks) == self.settings.width * self.settings.height:
                        break  # no free space for food

            self.parent.update()

            # Step 4. Send states
            self.parent.sendGameState()
        except Exception as e:
            print("tick", e)

    def getOccupiedBlocks(self):
        occupied_blocks = [i for i in self.food]
        occupied_blocks.extend([self.snakeToTorPos(s) for s in self.snakes])
        for s in self.snakes:
            occupied_blocks.extend([(x % self.settings.width, y % self.settings.height) for x, y in s.tail])
        return occupied_blocks

    def getPosForNewSnake(self):
        k = 30
        occupied_blocks = self.getOccupiedBlocks()
        f = lambda x, y: (x % self.settings.width, y % self.settings.height)
        while k:
            k -= 1
            x, y = random.randint(0, self.settings.width - 1), random.randint(0, self.settings.height - 1)
            is_occupied = False
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if f(x + dx, y + dy) in occupied_blocks:
                        is_occupied = True
            if not is_occupied:
                return x, y
        return None

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
            print("draw", e)

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
                    QColor("blue") if snake.player.id == self.client_id else QColor("red")
                )
                for tail_block in snake.tail:
                    painter.fillRect(
                        a + (tail_block[0] % self.settings.width) * base,
                        b + (tail_block[1] % self.settings.height) * base,
                        base, base,
                        QColor("aqua") if snake.player.id == self.client_id else QColor("pink")
                    )
        except Exception as e:
            print("drawSnakes", e)

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

import random

from google.protobuf.internal.containers import RepeatedCompositeFieldContainer

import task4.snakes.snakes_pb2 as snakes
from typing import Union, List, Tuple, Iterable, Set, Dict
import logging


class Snake:
    steer_block = {
        snakes.Direction.DOWN: snakes.Direction.UP,
        snakes.Direction.UP: snakes.Direction.DOWN,
        snakes.Direction.LEFT: snakes.Direction.RIGHT,
        snakes.Direction.RIGHT: snakes.Direction.LEFT,
    }

    def __init__(
            self,
            player_id: int,
            head_x: int,
            head_y: int,
            direction: snakes.Direction = snakes.UP,
            state: snakes.GameState.Snake.SnakeState = snakes.GameState.Snake.SnakeState.ALIVE,
    ):
        self.player_id = player_id
        self.state = state
        self.direction = direction
        self._requested_direction = None

        self.head_x = head_x
        self.head_y = head_y
        self.tail = list()
        match self.direction:
            case snakes.Direction.UP:
                self.tail.append((self.head_x, self.head_y + 1))
            case snakes.Direction.DOWN:
                self.tail.append((self.head_x, self.head_y - 1))
            case snakes.Direction.LEFT:
                self.tail.append((self.head_x + 1, self.head_y))
            case snakes.Direction.RIGHT:
                self.tail.append((self.head_x - 1, self.head_y))

    def toPoints(self, width: int, height: int) -> List[Tuple[int, int]]:
        points = list()
        old_x, old_y = self.head_x % width, self.head_y % height
        points.append((old_x, old_y))
        for x, y in self.tail:
            dx, dy = (x % width) - old_x, (y % height) - old_y
            points.append((dx, dy))
            old_x, old_y = x, y
        return points

    def fromPoints(self, points: Union[List[Tuple[int, int]], Iterable[snakes.GameState.Coord]]) -> None:
        if len(points) < 2:
            logging.warning("Snake's length is less than 2, something is very wrong!!")
            return
        head: Union[Tuple[int, int], snakes.GameState.Coord] = points[0]
        if type(head) is snakes.GameState.Coord:
            old_x, old_y = head.x, head.y
        else:
            old_x, old_y = head
        self.head_x, self.head_y = old_x, old_y
        self.tail.clear()
        for point in points[1:]:
            point: Union[Tuple[int, int], snakes.GameState.Coord] = point
            if type(point) is snakes.GameState.Coord:
                dx, dy = point.x, point.y
            else:
                dx, dy = point
            old_x, old_y = (old_x + dx, old_y + dy)
            self.tail.append((old_x, old_y))

    def asMsg(self, width: int, height: int):
        points = list(map(
                lambda point: snakes.GameState.Coord(x=point[0], y=point[1]),
                self.toPoints(width, height)
        ))
        return snakes.GameState.Snake(
            player_id=self.player_id,
            points=points,
            head_direction=self.direction,
            state=self.state
        )

    def turn(self, direction: snakes.Direction):
        self._requested_direction = direction

    def move(self):
        new_x, new_y = self.head_x, self.head_y
        if self._requested_direction is not None:
            self.direction = self._requested_direction
            self._requested_direction = None
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
        self.tail = [(self.head_x, self.head_y)] + self.tail[:-1]
        self.head_x, self.head_y = new_x, new_y
        return last


class FieldManager:
    UPDATE_SCORE = 1
    UPDATE_DEATH = 2

    def __init__(self, width: int, height: int, food_static: int):
        self.width = width
        self.height = height
        self.food_static = food_static
        self._snakes: Set[Snake] = set()
        self._food: Set[Tuple[int, int]] = set()

    def getSnakes(self) -> Set[Snake]:
        return self._snakes.copy()

    def getFood(self) -> Set[Tuple[int, int]]:
        return self._food.copy()

    def foodFromMsg(self, foods: RepeatedCompositeFieldContainer[snakes.GameState.Coord]):
        self._food.clear()
        for coord in foods:
            self._food.add((coord.x, coord.y))

    def snakesFromMsg(self, message_snakes: RepeatedCompositeFieldContainer[snakes.GameState.Snake]):
        alive_ids = set()
        for snake in message_snakes:
            alive_ids.add(snake.player_id)
            for old_snake in self._snakes:
                if old_snake.player_id == snake.player_id:
                    old_snake.direction = snake.head_direction
                    old_snake.fromPoints(snake.points)
                    break
            else:
                new_snake = Snake(
                    player_id=snake.player_id,
                    direction=snake.head_direction,
                    head_x=0, head_y=0,  # fromPoints() will fix that
                    state=snake.state
                )
                new_snake.fromPoints(snake.points)
                self._snakes.add(new_snake)

        self._snakes = set(filter(lambda snake: snake.player_id in alive_ids, self._snakes))

    def spawnSnake(
            self,
            x: int,
            y: int,
            player_id: int,
            state: snakes.GameState.Snake.SnakeState = snakes.GameState.Snake.SnakeState.ALIVE
    ) -> None:
        snake = Snake(
            player_id=player_id,
            head_x=x, head_y=y,
            direction=random.choice(
                [snakes.Direction.UP, snakes.Direction.DOWN, snakes.Direction.LEFT, snakes.Direction.RIGHT]
            ),
            state=state
        )
        self._snakes.add(snake)

    def getPosForNewSnake(self) -> Union[Tuple[int, int], None]:
        def f(lx, ly): return lx % self.width, ly % self.height
        k = 30
        occupied_blocks = self._getOccupiedBlocks()
        while k:
            k -= 1
            x, y = random.randint(0, self.width - 1), random.randint(0, self.height - 1)
            is_occupied = False
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if f(x + dx, y + dy) in occupied_blocks:
                        is_occupied = True
            if not is_occupied:
                return x, y
        return None

    def tick(self) -> Set[Tuple[int, int]]:
        updates: Set[Tuple[int, int]] = set()

        # Step 1. Food Update
        food_updates = self._tickFood()
        updates.update(food_updates)

        # Step 2. Death Update
        death_updates = self._tickDeath()
        updates.update(death_updates)

        # Step 3. Spawn Food
        self._replenishFood()
        return updates

    def _tickFood(self) -> Set[Tuple[int, int]]:
        updates: Set[Tuple[int, int]] = set()
        food_to_be_deleted = set()
        for snake in self._snakes:
            last = snake.move()
            pos = (snake.head_x % self.width, snake.head_y % self.height)
            if pos in self._food:
                food_to_be_deleted.add(pos)
                snake.tail.append(last)
                updates.add((snake.player_id, FieldManager.UPDATE_SCORE))

        self._food.difference_update(food_to_be_deleted)
        return updates

    def _tickDeath(self) -> Set[Tuple[int, int]]:
        updates: Set[Tuple[int, int]] = set()
        killing_blocks: Dict[Tuple[int, int], List[Snake]] = dict()

        for snake in self._snakes:
            head_pos = (snake.head_x % self.width, snake.head_y % self.height)
            if head_pos not in killing_blocks.keys():
                killing_blocks[head_pos] = list()
            killing_blocks[head_pos].append(snake)
            for x, y in snake.tail:
                pos = (x % self.width, y % self.height)
                if pos not in killing_blocks.keys():
                    killing_blocks[pos] = list()
                killing_blocks[pos].append(snake)

        dead_snakes = set()
        for snake in self._snakes:
            head_pos = (snake.head_x % self.width, snake.head_y % self.height)
            if head_pos in killing_blocks.keys():
                killers = [s for s in killing_blocks[head_pos]]
                killers.remove(snake)
                if len(killers) == 0:
                    continue
                for killer in killers:
                    if killer != snake:
                        updates.add((snake.player_id, FieldManager.UPDATE_SCORE))

                dead_snakes.add(snake)
                self._spawnFoodFromSnake(snake)
                updates.add((snake.player_id, FieldManager.UPDATE_DEATH))

        for snake in dead_snakes:
            self._snakes.remove(snake)
        return updates

    def _spawnFoodFromSnake(self, snake: Snake) -> None:
        snake_blocks = [(x % self.width, y % self.height) for x, y in snake.tail]

        for block in snake_blocks:
            a = random.random()
            if a < 0.5:
                self._food.add(block)

    def _replenishFood(self) -> None:
        if len(self._food) < self.food_static + len(self._snakes):
            occupied_blocks = self._getOccupiedBlocks()
            while len(self._food) < self.food_static + len(self._snakes):
                occupied_blocks.add(self._spawnFood(occupied_blocks))
                if len(occupied_blocks) == self.width * self.height:
                    break  # no free space for food

    def _spawnFood(self, occupied_blocks: set = None) -> Tuple[int, int]:
        if occupied_blocks is None:
            occupied_blocks = set()

        while True:
            x, y = random.randint(0, self.width - 1), random.randint(0, self.height - 1)
            if (x, y) not in occupied_blocks:
                self._food.add((x, y))
                return x, y

    def _getOccupiedBlocks(self):
        occupied_blocks = self._food.copy()
        for snake in self._snakes:
            occupied_blocks.add((snake.head_x % self.width, snake.head_y % self.height))
            for x, y in snake.tail:
                occupied_blocks.add((x % self.width, y % self.height))
        return occupied_blocks

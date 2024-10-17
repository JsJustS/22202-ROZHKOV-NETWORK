from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class NodeRole(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NORMAL: _ClassVar[NodeRole]
    MASTER: _ClassVar[NodeRole]
    DEPUTY: _ClassVar[NodeRole]
    VIEWER: _ClassVar[NodeRole]

class PlayerType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    HUMAN: _ClassVar[PlayerType]
    ROBOT: _ClassVar[PlayerType]

class Direction(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UP: _ClassVar[Direction]
    DOWN: _ClassVar[Direction]
    LEFT: _ClassVar[Direction]
    RIGHT: _ClassVar[Direction]
NORMAL: NodeRole
MASTER: NodeRole
DEPUTY: NodeRole
VIEWER: NodeRole
HUMAN: PlayerType
ROBOT: PlayerType
UP: Direction
DOWN: Direction
LEFT: Direction
RIGHT: Direction

class GamePlayer(_message.Message):
    __slots__ = ("name", "id", "ip_address", "port", "role", "type", "score")
    NAME_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    name: str
    id: int
    ip_address: str
    port: int
    role: NodeRole
    type: PlayerType
    score: int
    def __init__(self, name: _Optional[str] = ..., id: _Optional[int] = ..., ip_address: _Optional[str] = ..., port: _Optional[int] = ..., role: _Optional[_Union[NodeRole, str]] = ..., type: _Optional[_Union[PlayerType, str]] = ..., score: _Optional[int] = ...) -> None: ...

class GameConfig(_message.Message):
    __slots__ = ("width", "height", "food_static", "state_delay_ms")
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    FOOD_STATIC_FIELD_NUMBER: _ClassVar[int]
    STATE_DELAY_MS_FIELD_NUMBER: _ClassVar[int]
    width: int
    height: int
    food_static: int
    state_delay_ms: int
    def __init__(self, width: _Optional[int] = ..., height: _Optional[int] = ..., food_static: _Optional[int] = ..., state_delay_ms: _Optional[int] = ...) -> None: ...

class GamePlayers(_message.Message):
    __slots__ = ("players",)
    PLAYERS_FIELD_NUMBER: _ClassVar[int]
    players: _containers.RepeatedCompositeFieldContainer[GamePlayer]
    def __init__(self, players: _Optional[_Iterable[_Union[GamePlayer, _Mapping]]] = ...) -> None: ...

class GameState(_message.Message):
    __slots__ = ("state_order", "snakes", "foods", "players")
    class Coord(_message.Message):
        __slots__ = ("x", "y")
        X_FIELD_NUMBER: _ClassVar[int]
        Y_FIELD_NUMBER: _ClassVar[int]
        x: int
        y: int
        def __init__(self, x: _Optional[int] = ..., y: _Optional[int] = ...) -> None: ...
    class Snake(_message.Message):
        __slots__ = ("player_id", "points", "state", "head_direction")
        class SnakeState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            ALIVE: _ClassVar[GameState.Snake.SnakeState]
            ZOMBIE: _ClassVar[GameState.Snake.SnakeState]
        ALIVE: GameState.Snake.SnakeState
        ZOMBIE: GameState.Snake.SnakeState
        PLAYER_ID_FIELD_NUMBER: _ClassVar[int]
        POINTS_FIELD_NUMBER: _ClassVar[int]
        STATE_FIELD_NUMBER: _ClassVar[int]
        HEAD_DIRECTION_FIELD_NUMBER: _ClassVar[int]
        player_id: int
        points: _containers.RepeatedCompositeFieldContainer[GameState.Coord]
        state: GameState.Snake.SnakeState
        head_direction: Direction
        def __init__(self, player_id: _Optional[int] = ..., points: _Optional[_Iterable[_Union[GameState.Coord, _Mapping]]] = ..., state: _Optional[_Union[GameState.Snake.SnakeState, str]] = ..., head_direction: _Optional[_Union[Direction, str]] = ...) -> None: ...
    STATE_ORDER_FIELD_NUMBER: _ClassVar[int]
    SNAKES_FIELD_NUMBER: _ClassVar[int]
    FOODS_FIELD_NUMBER: _ClassVar[int]
    PLAYERS_FIELD_NUMBER: _ClassVar[int]
    state_order: int
    snakes: _containers.RepeatedCompositeFieldContainer[GameState.Snake]
    foods: _containers.RepeatedCompositeFieldContainer[GameState.Coord]
    players: GamePlayers
    def __init__(self, state_order: _Optional[int] = ..., snakes: _Optional[_Iterable[_Union[GameState.Snake, _Mapping]]] = ..., foods: _Optional[_Iterable[_Union[GameState.Coord, _Mapping]]] = ..., players: _Optional[_Union[GamePlayers, _Mapping]] = ...) -> None: ...

class GameAnnouncement(_message.Message):
    __slots__ = ("players", "config", "can_join", "game_name")
    PLAYERS_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    CAN_JOIN_FIELD_NUMBER: _ClassVar[int]
    GAME_NAME_FIELD_NUMBER: _ClassVar[int]
    players: GamePlayers
    config: GameConfig
    can_join: bool
    game_name: str
    def __init__(self, players: _Optional[_Union[GamePlayers, _Mapping]] = ..., config: _Optional[_Union[GameConfig, _Mapping]] = ..., can_join: bool = ..., game_name: _Optional[str] = ...) -> None: ...

class GameMessage(_message.Message):
    __slots__ = ("msg_seq", "sender_id", "receiver_id", "ping", "steer", "ack", "state", "announcement", "join", "error", "role_change", "discover")
    class PingMsg(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...
    class SteerMsg(_message.Message):
        __slots__ = ("direction",)
        DIRECTION_FIELD_NUMBER: _ClassVar[int]
        direction: Direction
        def __init__(self, direction: _Optional[_Union[Direction, str]] = ...) -> None: ...
    class AckMsg(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...
    class StateMsg(_message.Message):
        __slots__ = ("state",)
        STATE_FIELD_NUMBER: _ClassVar[int]
        state: GameState
        def __init__(self, state: _Optional[_Union[GameState, _Mapping]] = ...) -> None: ...
    class AnnouncementMsg(_message.Message):
        __slots__ = ("games",)
        GAMES_FIELD_NUMBER: _ClassVar[int]
        games: _containers.RepeatedCompositeFieldContainer[GameAnnouncement]
        def __init__(self, games: _Optional[_Iterable[_Union[GameAnnouncement, _Mapping]]] = ...) -> None: ...
    class DiscoverMsg(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...
    class JoinMsg(_message.Message):
        __slots__ = ("player_type", "player_name", "game_name", "requested_role")
        PLAYER_TYPE_FIELD_NUMBER: _ClassVar[int]
        PLAYER_NAME_FIELD_NUMBER: _ClassVar[int]
        GAME_NAME_FIELD_NUMBER: _ClassVar[int]
        REQUESTED_ROLE_FIELD_NUMBER: _ClassVar[int]
        player_type: PlayerType
        player_name: str
        game_name: str
        requested_role: NodeRole
        def __init__(self, player_type: _Optional[_Union[PlayerType, str]] = ..., player_name: _Optional[str] = ..., game_name: _Optional[str] = ..., requested_role: _Optional[_Union[NodeRole, str]] = ...) -> None: ...
    class ErrorMsg(_message.Message):
        __slots__ = ("error_message",)
        ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
        error_message: str
        def __init__(self, error_message: _Optional[str] = ...) -> None: ...
    class RoleChangeMsg(_message.Message):
        __slots__ = ("sender_role", "receiver_role")
        SENDER_ROLE_FIELD_NUMBER: _ClassVar[int]
        RECEIVER_ROLE_FIELD_NUMBER: _ClassVar[int]
        sender_role: NodeRole
        receiver_role: NodeRole
        def __init__(self, sender_role: _Optional[_Union[NodeRole, str]] = ..., receiver_role: _Optional[_Union[NodeRole, str]] = ...) -> None: ...
    MSG_SEQ_FIELD_NUMBER: _ClassVar[int]
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_ID_FIELD_NUMBER: _ClassVar[int]
    PING_FIELD_NUMBER: _ClassVar[int]
    STEER_FIELD_NUMBER: _ClassVar[int]
    ACK_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    ANNOUNCEMENT_FIELD_NUMBER: _ClassVar[int]
    JOIN_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    ROLE_CHANGE_FIELD_NUMBER: _ClassVar[int]
    DISCOVER_FIELD_NUMBER: _ClassVar[int]
    msg_seq: int
    sender_id: int
    receiver_id: int
    ping: GameMessage.PingMsg
    steer: GameMessage.SteerMsg
    ack: GameMessage.AckMsg
    state: GameMessage.StateMsg
    announcement: GameMessage.AnnouncementMsg
    join: GameMessage.JoinMsg
    error: GameMessage.ErrorMsg
    role_change: GameMessage.RoleChangeMsg
    discover: GameMessage.DiscoverMsg
    def __init__(self, msg_seq: _Optional[int] = ..., sender_id: _Optional[int] = ..., receiver_id: _Optional[int] = ..., ping: _Optional[_Union[GameMessage.PingMsg, _Mapping]] = ..., steer: _Optional[_Union[GameMessage.SteerMsg, _Mapping]] = ..., ack: _Optional[_Union[GameMessage.AckMsg, _Mapping]] = ..., state: _Optional[_Union[GameMessage.StateMsg, _Mapping]] = ..., announcement: _Optional[_Union[GameMessage.AnnouncementMsg, _Mapping]] = ..., join: _Optional[_Union[GameMessage.JoinMsg, _Mapping]] = ..., error: _Optional[_Union[GameMessage.ErrorMsg, _Mapping]] = ..., role_change: _Optional[_Union[GameMessage.RoleChangeMsg, _Mapping]] = ..., discover: _Optional[_Union[GameMessage.DiscoverMsg, _Mapping]] = ...) -> None: ...

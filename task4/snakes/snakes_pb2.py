# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: snakes.proto
# Protobuf Python Version: 5.28.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    28,
    2,
    '',
    'snakes.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0csnakes.proto\x12\x06snakes\"\xa0\x01\n\nGamePlayer\x12\x0c\n\x04name\x18\x01 \x02(\t\x12\n\n\x02id\x18\x02 \x02(\x05\x12\x12\n\nip_address\x18\x03 \x01(\t\x12\x0c\n\x04port\x18\x04 \x01(\x05\x12\x1e\n\x04role\x18\x05 \x02(\x0e\x32\x10.snakes.NodeRole\x12\'\n\x04type\x18\x06 \x01(\x0e\x32\x12.snakes.PlayerType:\x05HUMAN\x12\r\n\x05score\x18\x07 \x02(\x05\"i\n\nGameConfig\x12\x11\n\x05width\x18\x01 \x01(\x05:\x02\x34\x30\x12\x12\n\x06height\x18\x02 \x01(\x05:\x02\x33\x30\x12\x16\n\x0b\x66ood_static\x18\x03 \x01(\x05:\x01\x31\x12\x1c\n\x0estate_delay_ms\x18\x05 \x01(\x05:\x04\x31\x30\x30\x30\"2\n\x0bGamePlayers\x12#\n\x07players\x18\x01 \x03(\x0b\x32\x12.snakes.GamePlayer\"\x8c\x03\n\tGameState\x12\x13\n\x0bstate_order\x18\x01 \x02(\x05\x12\'\n\x06snakes\x18\x02 \x03(\x0b\x32\x17.snakes.GameState.Snake\x12&\n\x05\x66oods\x18\x03 \x03(\x0b\x32\x17.snakes.GameState.Coord\x12$\n\x07players\x18\x04 \x02(\x0b\x32\x13.snakes.GamePlayers\x1a#\n\x05\x43oord\x12\x0c\n\x01x\x18\x01 \x01(\x11:\x01\x30\x12\x0c\n\x01y\x18\x02 \x01(\x11:\x01\x30\x1a\xcd\x01\n\x05Snake\x12\x11\n\tplayer_id\x18\x01 \x02(\x05\x12\'\n\x06points\x18\x02 \x03(\x0b\x32\x17.snakes.GameState.Coord\x12\x38\n\x05state\x18\x03 \x02(\x0e\x32\".snakes.GameState.Snake.SnakeState:\x05\x41LIVE\x12)\n\x0ehead_direction\x18\x04 \x02(\x0e\x32\x11.snakes.Direction\"#\n\nSnakeState\x12\t\n\x05\x41LIVE\x10\x00\x12\n\n\x06ZOMBIE\x10\x01\"\x87\x01\n\x10GameAnnouncement\x12$\n\x07players\x18\x01 \x02(\x0b\x32\x13.snakes.GamePlayers\x12\"\n\x06\x63onfig\x18\x02 \x02(\x0b\x32\x12.snakes.GameConfig\x12\x16\n\x08\x63\x61n_join\x18\x03 \x01(\x08:\x04true\x12\x11\n\tgame_name\x18\x04 \x02(\t\"\xde\x07\n\x0bGameMessage\x12\x0f\n\x07msg_seq\x18\x01 \x02(\x03\x12\x11\n\tsender_id\x18\n \x01(\x05\x12\x13\n\x0breceiver_id\x18\x0b \x01(\x05\x12+\n\x04ping\x18\x02 \x01(\x0b\x32\x1b.snakes.GameMessage.PingMsgH\x00\x12-\n\x05steer\x18\x03 \x01(\x0b\x32\x1c.snakes.GameMessage.SteerMsgH\x00\x12)\n\x03\x61\x63k\x18\x04 \x01(\x0b\x32\x1a.snakes.GameMessage.AckMsgH\x00\x12-\n\x05state\x18\x05 \x01(\x0b\x32\x1c.snakes.GameMessage.StateMsgH\x00\x12;\n\x0c\x61nnouncement\x18\x06 \x01(\x0b\x32#.snakes.GameMessage.AnnouncementMsgH\x00\x12+\n\x04join\x18\x07 \x01(\x0b\x32\x1b.snakes.GameMessage.JoinMsgH\x00\x12-\n\x05\x65rror\x18\x08 \x01(\x0b\x32\x1c.snakes.GameMessage.ErrorMsgH\x00\x12\x38\n\x0brole_change\x18\t \x01(\x0b\x32!.snakes.GameMessage.RoleChangeMsgH\x00\x12\x33\n\x08\x64iscover\x18\x0c \x01(\x0b\x32\x1f.snakes.GameMessage.DiscoverMsgH\x00\x1a\t\n\x07PingMsg\x1a\x30\n\x08SteerMsg\x12$\n\tdirection\x18\x01 \x02(\x0e\x32\x11.snakes.Direction\x1a\x08\n\x06\x41\x63kMsg\x1a,\n\x08StateMsg\x12 \n\x05state\x18\x01 \x02(\x0b\x32\x11.snakes.GameState\x1a:\n\x0f\x41nnouncementMsg\x12\'\n\x05games\x18\x01 \x03(\x0b\x32\x18.snakes.GameAnnouncement\x1a\r\n\x0b\x44iscoverMsg\x1a\x8b\x01\n\x07JoinMsg\x12.\n\x0bplayer_type\x18\x01 \x01(\x0e\x32\x12.snakes.PlayerType:\x05HUMAN\x12\x13\n\x0bplayer_name\x18\x03 \x02(\t\x12\x11\n\tgame_name\x18\x04 \x02(\t\x12(\n\x0erequested_role\x18\x05 \x02(\x0e\x32\x10.snakes.NodeRole\x1a!\n\x08\x45rrorMsg\x12\x15\n\rerror_message\x18\x01 \x02(\t\x1a_\n\rRoleChangeMsg\x12%\n\x0bsender_role\x18\x01 \x01(\x0e\x32\x10.snakes.NodeRole\x12\'\n\rreceiver_role\x18\x02 \x01(\x0e\x32\x10.snakes.NodeRoleB\x06\n\x04Type*:\n\x08NodeRole\x12\n\n\x06NORMAL\x10\x00\x12\n\n\x06MASTER\x10\x01\x12\n\n\x06\x44\x45PUTY\x10\x02\x12\n\n\x06VIEWER\x10\x03*\"\n\nPlayerType\x12\t\n\x05HUMAN\x10\x00\x12\t\n\x05ROBOT\x10\x01*2\n\tDirection\x12\x06\n\x02UP\x10\x01\x12\x08\n\x04\x44OWN\x10\x02\x12\x08\n\x04LEFT\x10\x03\x12\t\n\x05RIGHT\x10\x04\x42&\n\x17me.ippolitov.fit.snakesB\x0bSnakesProto')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'snakes_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  _globals['DESCRIPTOR']._loaded_options = None
  _globals['DESCRIPTOR']._serialized_options = b'\n\027me.ippolitov.fit.snakesB\013SnakesProto'
  _globals['_NODEROLE']._serialized_start=1876
  _globals['_NODEROLE']._serialized_end=1934
  _globals['_PLAYERTYPE']._serialized_start=1936
  _globals['_PLAYERTYPE']._serialized_end=1970
  _globals['_DIRECTION']._serialized_start=1972
  _globals['_DIRECTION']._serialized_end=2022
  _globals['_GAMEPLAYER']._serialized_start=25
  _globals['_GAMEPLAYER']._serialized_end=185
  _globals['_GAMECONFIG']._serialized_start=187
  _globals['_GAMECONFIG']._serialized_end=292
  _globals['_GAMEPLAYERS']._serialized_start=294
  _globals['_GAMEPLAYERS']._serialized_end=344
  _globals['_GAMESTATE']._serialized_start=347
  _globals['_GAMESTATE']._serialized_end=743
  _globals['_GAMESTATE_COORD']._serialized_start=500
  _globals['_GAMESTATE_COORD']._serialized_end=535
  _globals['_GAMESTATE_SNAKE']._serialized_start=538
  _globals['_GAMESTATE_SNAKE']._serialized_end=743
  _globals['_GAMESTATE_SNAKE_SNAKESTATE']._serialized_start=708
  _globals['_GAMESTATE_SNAKE_SNAKESTATE']._serialized_end=743
  _globals['_GAMEANNOUNCEMENT']._serialized_start=746
  _globals['_GAMEANNOUNCEMENT']._serialized_end=881
  _globals['_GAMEMESSAGE']._serialized_start=884
  _globals['_GAMEMESSAGE']._serialized_end=1874
  _globals['_GAMEMESSAGE_PINGMSG']._serialized_start=1402
  _globals['_GAMEMESSAGE_PINGMSG']._serialized_end=1411
  _globals['_GAMEMESSAGE_STEERMSG']._serialized_start=1413
  _globals['_GAMEMESSAGE_STEERMSG']._serialized_end=1461
  _globals['_GAMEMESSAGE_ACKMSG']._serialized_start=1463
  _globals['_GAMEMESSAGE_ACKMSG']._serialized_end=1471
  _globals['_GAMEMESSAGE_STATEMSG']._serialized_start=1473
  _globals['_GAMEMESSAGE_STATEMSG']._serialized_end=1517
  _globals['_GAMEMESSAGE_ANNOUNCEMENTMSG']._serialized_start=1519
  _globals['_GAMEMESSAGE_ANNOUNCEMENTMSG']._serialized_end=1577
  _globals['_GAMEMESSAGE_DISCOVERMSG']._serialized_start=1579
  _globals['_GAMEMESSAGE_DISCOVERMSG']._serialized_end=1592
  _globals['_GAMEMESSAGE_JOINMSG']._serialized_start=1595
  _globals['_GAMEMESSAGE_JOINMSG']._serialized_end=1734
  _globals['_GAMEMESSAGE_ERRORMSG']._serialized_start=1736
  _globals['_GAMEMESSAGE_ERRORMSG']._serialized_end=1769
  _globals['_GAMEMESSAGE_ROLECHANGEMSG']._serialized_start=1771
  _globals['_GAMEMESSAGE_ROLECHANGEMSG']._serialized_end=1866
# @@protoc_insertion_point(module_scope)

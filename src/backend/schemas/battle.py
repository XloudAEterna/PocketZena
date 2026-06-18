from pydantic import BaseModel, Field
from typing import List, Optional


class TeamZenamonStatus(BaseModel):
    position: int
    name: str
    current_hp: int
    max_hp: int
    is_active: bool
    is_fainted: bool


class PlayerBattleStatus(BaseModel):
    nickname: str
    active_zenamon_name: Optional[str] = None
    active_zenamon_hp: Optional[int] = None
    active_zenamon_max_hp: Optional[int] = None
    active_zenamon_sprite: Optional[str] = None
    active_zenamon_is_fainted: bool = False
    team: List[TeamZenamonStatus] = Field(default_factory=list)
    is_ready: bool


class ReactionStatus(BaseModel):
    id: int
    emoji: str


class BattleStatusResponse(BaseModel):
    status: str
    current_turn: int
    player1: PlayerBattleStatus
    player2: PlayerBattleStatus
    new_events: List[str]
    reactions: List[ReactionStatus]
    winner_id: Optional[int] = None
    winner_nickname: Optional[str] = None


class BattleAction(BaseModel):
    type: str
    move_name: Optional[str] = None
    zenamon_index: Optional[int] = None


class ReactionCreate(BaseModel):
    emoji: str
    target_player_id: Optional[int] = None

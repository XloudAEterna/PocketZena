from pydantic import BaseModel
from typing import List, Optional

class PlayerBattleStatus(BaseModel):
    nickname: str
    active_zenamon_name: Optional[str] = None
    active_zenamon_hp: Optional[int] = None
    active_zenamon_max_hp: Optional[int] = None
    active_zenamon_sprite: Optional[str] = None
    is_ready: bool # Se ha già inviato l'azione per il turno corrente

class BattleStatusResponse(BaseModel):
    status: str
    current_turn: int
    player1: PlayerBattleStatus
    player2: PlayerBattleStatus
    new_events: List[str]
    reactions: List[str]
    winner_nickname: Optional[str] = None

class BattleAction(BaseModel):
    type: str # ATTACK, SWITCH
    move_name: Optional[str] = None
    zenamon_index: Optional[int] = None # 1, 2, 3 per lo switch

class ReactionCreate(BaseModel):
    emoji: str
    target_player_id: Optional[int] = None

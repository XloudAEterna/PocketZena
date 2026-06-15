from pydantic import BaseModel, ConfigDict
from typing import List

class MoveResponse(BaseModel):
    name: str
    power: int
    type: str
    damage_class: str

class ZenamonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    types: List[str]
    sprite: str
    moves: List[MoveResponse]

class TeamCreate(BaseModel):
    zenamon_ids: List[int] # Devono essere esattamente 3

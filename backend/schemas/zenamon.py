from pydantic import BaseModel
from typing import List

class MoveResponse(BaseModel):
    name: str
    power: int
    type: str
    damage_class: str

class ZenamonResponse(BaseModel):
    id: int
    name: str
    types: List[str]
    sprite: str
    moves: List[MoveResponse]

    class Config:
        from_attributes = True

class TeamCreate(BaseModel):
    zenamon_ids: List[int] # Devono essere esattamente 3

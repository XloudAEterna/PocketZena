from pydantic import BaseModel
from typing import Optional

class DuelCreateResponse(BaseModel):
    duel_code: str
    status: str

class DuelJoinResponse(BaseModel):
    success: bool
    status: str

class DuelSpectateResponse(BaseModel):
    success: bool
    role: str

from pydantic import BaseModel, Field, ConfigDict

class PlayerCreate(BaseModel):
    nickname: str = Field(..., min_length=3, max_length=3, pattern="^[A-Z0-9]+$")

class PlayerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    nickname: str
    token: str

from pydantic import BaseModel, Field

class PlayerCreate(BaseModel):
    nickname: str = Field(..., min_length=3, max_length=3, pattern="^[A-Z]{3}$")

class PlayerResponse(BaseModel):
    id: int
    nickname: str
    token: str

    class Config:
        from_attributes = True

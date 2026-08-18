from datetime import datetime

from pydantic import BaseModel


class CatchCreate(BaseModel):
    species: str
    weight: float | None = None
    length: float | None = None
    location: str
    date_caught: datetime

class CatchResponse(BaseModel):
    id: int
    species: str
    weight: float | None
    length: float | None
    location: str
    date_caught: datetime

    model_config = {"from_attributes": True}
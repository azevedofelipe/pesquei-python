from datetime import datetime

from pydantic import BaseModel


class CatchCreate(BaseModel):
    date_caught: datetime = datetime.now()
    species: str | None = None
    weight: float | None = None
    length: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    lure_id: int | None = None
    depth: float | None = None
    notes: str | None = None


class CatchUpdate(BaseModel):
    date_caught: datetime | None = None
    species: str | None = None
    weight: float | None = None
    length: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    lure_id: int | None = None
    depth: float | None = None
    notes: str | None = None


class CatchResponse(BaseModel):
    id: int
    user_id: int
    species: str | None
    weight: float | None
    length: float | None
    latitude: float | None
    longitude: float | None
    date_caught: datetime
    lure_id: int | None
    depth: float | None
    notes: str | None

    model_config = {"from_attributes": True}
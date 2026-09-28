from datetime import datetime, timezone

from pydantic import BaseModel, Field


class CatchCreate(BaseModel):
    date_caught: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
    # Weather snapshot captured at creation time (best-effort — see
    # POST /catch/, null if the Open-Meteo lookup failed or the catch has no
    # latitude/longitude). Not part of CatchCreate/CatchUpdate: these are
    # server-computed, not user-supplied.
    temperature: float | None
    conditions: str | None
    sunrise: datetime | None
    sunset: datetime | None

    model_config = {"from_attributes": True}
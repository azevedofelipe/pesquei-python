from pydantic import BaseModel


class LureCreate(BaseModel):
    name: str | None = None
    weight: float | None = None
    type: str | None = None
    color: str | None = None
    brand: str | None = None
    model: str | None = None
    size: float | None = None


class LureUpdate(BaseModel):
    name: str | None = None
    weight: float | None = None
    type: str | None = None
    color: str | None = None
    brand: str | None = None
    model: str | None = None
    size: float | None = None


class LureResponse(BaseModel):
    id: int
    user_id: int
    name: str | None
    weight: float | None
    type: str | None
    color: str | None
    brand: str | None
    model: str | None
    size: float | None

    model_config = {"from_attributes": True}
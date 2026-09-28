from decimal import Decimal

from pydantic import BaseModel


class LureCreate(BaseModel):
    name: str | None = None
    weight: Decimal | None = None
    type: str | None = None
    color: str | None = None
    brand: str | None = None
    model: str | None = None
    size: Decimal | None = None


class LureResponse(BaseModel):
    id: int
    user_id: int
    name: str | None
    weight: Decimal | None
    type: str | None
    color: str | None
    brand: str | None
    model: str | None
    size: Decimal | None

    model_config = {"from_attributes": True}
import datetime

from sqlalchemy import DateTime, Double, Integer, PrimaryKeyConstraint, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass


class Catch(Base):
    __tablename__ = 'catch'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='catch_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    species: Mapped[str] = mapped_column(String(50), nullable=False)
    weight: Mapped[float] = mapped_column(Double(53), nullable=False)
    length: Mapped[float] = mapped_column(Double(53), nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    date_caught: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

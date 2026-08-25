from typing import Optional
import datetime
import decimal

from sqlalchemy import DateTime, ForeignKeyConstraint, Integer, Numeric, PrimaryKeyConstraint, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class Lure(Base):
    __tablename__ = 'lure'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='lure_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String(50))
    weight: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(6, 2))
    type: Mapped[Optional[str]] = mapped_column(String(50))
    color: Mapped[Optional[str]] = mapped_column(String(100))
    brand: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[Optional[str]] = mapped_column(String(100))
    size: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(6, 2))

    catch: Mapped[list['Catch']] = relationship('Catch', back_populates='lure')


class Catch(Base):
    __tablename__ = 'catch'
    __table_args__ = (
        ForeignKeyConstraint(['lure_id'], ['lure.id'], name='catch_lure_id_fkey'),
        PrimaryKeyConstraint('id', name='catch_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date_caught: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    species: Mapped[Optional[str]] = mapped_column(String(50))
    weight: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(6, 2))
    length: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(6, 2))
    latitude: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(9, 6))
    lure_id: Mapped[Optional[int]] = mapped_column(Integer)
    depth: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(6, 2))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    lure: Mapped[Optional['Lure']] = relationship('Lure', back_populates='catch')

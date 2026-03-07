"""Queue and clearinghouse management tables."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from spb_shared.database import Base


class Fila(Base):
    """Message queue for payment processing (from Fila)."""

    __tablename__ = "fila"

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    valor: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    mensagem: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    tipo: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    contraparte: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    data: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    prdade: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    msg_xml: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Camaras(Base):
    """Clearinghouse balance summary (from Camaras)."""

    __tablename__ = "camaras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tot_str: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    tot_compe: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    tot_cip: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)

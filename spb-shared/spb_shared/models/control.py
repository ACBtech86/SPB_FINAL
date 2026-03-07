"""Control/status tables - matches BCSrvSqlMq schema."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from spb_shared.database import Base


class SPBControle(Base):
    """Local STR control/status table (controle table in BCSrvSqlMq)."""

    __tablename__ = "spb_controle"

    # Primary key is ispb (no autoincrement id)
    ispb: Mapped[str] = mapped_column(String(8), primary_key=True, nullable=False)
    nome_ispb: Mapped[str] = mapped_column(String(15), nullable=False)
    msg_seq: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    status_geral: Mapped[str] = mapped_column(String(1), nullable=False)
    dthr_eco: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ultmsg: Mapped[Optional[str]] = mapped_column(String(23), nullable=True)
    dthr_ultmsg: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    certificadora: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


class BacenControle(Base):
    """Remote BACEN control/status table (bacen_controle in BCSrvSqlMq)."""

    __tablename__ = "bacen_controle"

    # Primary key is ispb (no autoincrement id)
    ispb: Mapped[str] = mapped_column(String(8), primary_key=True, nullable=False)
    nome_ispb: Mapped[str] = mapped_column(String(15), nullable=False)
    msg_seq: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    status_geral: Mapped[str] = mapped_column(String(1), nullable=False)
    dthr_eco: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ultmsg: Mapped[Optional[str]] = mapped_column(String(23), nullable=True)
    dthr_ultmsg: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    certificadora: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

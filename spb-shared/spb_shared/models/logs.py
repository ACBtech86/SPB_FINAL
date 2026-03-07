"""System log tables - matches BCSrvSqlMq schema."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from spb_shared.database import Base


class SPBLogBacen(Base):
    """System event log for BACEN channel (str_log table in BCSrvSqlMq)."""

    __tablename__ = "spb_log_bacen"

    # Composite primary key: (db_datetime, mq_msg_id)
    mq_msg_id: Mapped[bytes] = mapped_column(LargeBinary, primary_key=True, nullable=False)
    mq_correl_id: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    db_datetime: Mapped[datetime] = mapped_column(DateTime, primary_key=True, nullable=False)
    status_msg: Mapped[str] = mapped_column(String(1), nullable=False)
    mq_qn_origem: Mapped[str] = mapped_column(String(48), nullable=False)
    mq_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    mq_header: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    security_header: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    nu_ope: Mapped[Optional[str]] = mapped_column(String(23), nullable=True)
    cod_msg: Mapped[Optional[str]] = mapped_column(String(9), nullable=True)
    msg: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (Index("ix1_spb_log_bacen", "nu_ope"),)


class SPBLogSelic(Base):
    """System event log for SELIC channel (str_log table in BCSrvSqlMq for SELIC)."""

    __tablename__ = "spb_log_selic"

    # Composite primary key: (db_datetime, mq_msg_id)
    mq_msg_id: Mapped[bytes] = mapped_column(LargeBinary, primary_key=True, nullable=False)
    mq_correl_id: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    db_datetime: Mapped[datetime] = mapped_column(DateTime, primary_key=True, nullable=False)
    status_msg: Mapped[str] = mapped_column(String(1), nullable=False)
    mq_qn_origem: Mapped[str] = mapped_column(String(48), nullable=False)
    mq_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    mq_header: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    security_header: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    nu_ope: Mapped[Optional[str]] = mapped_column(String(23), nullable=True)
    cod_msg: Mapped[Optional[str]] = mapped_column(String(9), nullable=True)
    msg: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (Index("ix1_spb_log_selic", "nu_ope"),)

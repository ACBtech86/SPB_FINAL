"""Message tables for SPB system - matches BCSrvSqlMq schema."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from spb_shared.database import Base


class SPBBacenToLocal(Base):
    """Inbound messages from BACEN (bacen_req table in BCSrvSqlMq)."""

    __tablename__ = "spb_bacen_to_local"

    # Composite primary key: (db_datetime, mq_msg_id)
    mq_msg_id: Mapped[bytes] = mapped_column(LargeBinary, primary_key=True, nullable=False)
    mq_correl_id: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    db_datetime: Mapped[datetime] = mapped_column(DateTime, primary_key=True, nullable=False)
    status_msg: Mapped[str] = mapped_column(String(1), nullable=False)
    flag_proc: Mapped[str] = mapped_column(String(1), nullable=False)
    mq_qn_origem: Mapped[str] = mapped_column(String(48), nullable=False)
    mq_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    mq_header: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    security_header: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    nu_ope: Mapped[Optional[str]] = mapped_column(String(23), nullable=True)
    cod_msg: Mapped[Optional[str]] = mapped_column(String(9), nullable=True)
    msg: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix1_spb_bacen_to_local", "nu_ope"),
        Index("ix2_spb_bacen_to_local", "flag_proc", "mq_qn_origem"),
    )


class SPBSelicToLocal(Base):
    """Inbound messages from SELIC (selic_req table in BCSrvSqlMq)."""

    __tablename__ = "spb_selic_to_local"

    # Composite primary key: (db_datetime, mq_msg_id)
    mq_msg_id: Mapped[bytes] = mapped_column(LargeBinary, primary_key=True, nullable=False)
    mq_correl_id: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    db_datetime: Mapped[datetime] = mapped_column(DateTime, primary_key=True, nullable=False)
    status_msg: Mapped[str] = mapped_column(String(1), nullable=False)
    flag_proc: Mapped[str] = mapped_column(String(1), nullable=False)
    mq_qn_origem: Mapped[str] = mapped_column(String(48), nullable=False)
    mq_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    mq_header: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    security_header: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    nu_ope: Mapped[Optional[str]] = mapped_column(String(23), nullable=True)
    cod_msg: Mapped[Optional[str]] = mapped_column(String(9), nullable=True)
    msg: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix1_spb_selic_to_local", "nu_ope"),
        Index("ix2_spb_selic_to_local", "flag_proc", "mq_qn_origem"),
    )


class SPBLocalToBacen(Base):
    """Outbound messages to BACEN (if_req table in BCSrvSqlMq)."""

    __tablename__ = "spb_local_to_bacen"

    # Composite primary key: (db_datetime, mq_msg_id) - matches actual database
    mq_msg_id: Mapped[bytes] = mapped_column(LargeBinary, primary_key=True, nullable=False)
    mq_correl_id: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    db_datetime: Mapped[datetime] = mapped_column(DateTime, primary_key=True, nullable=False)
    status_msg: Mapped[str] = mapped_column(String(1), nullable=False)
    flag_proc: Mapped[str] = mapped_column(String(1), nullable=False)
    mq_qn_origem: Mapped[str] = mapped_column(String(48), nullable=False)
    mq_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    mq_header: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    security_header: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    nu_ope: Mapped[Optional[str]] = mapped_column(String(23), nullable=True)
    cod_msg: Mapped[Optional[str]] = mapped_column(String(9), nullable=True)
    msg: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix1_spb_local_to_bacen", "nu_ope"),
        Index("ix2_spb_local_to_bacen", "flag_proc", "mq_qn_origem"),
    )


class SPBLocalToSelic(Base):
    """Outbound messages to SELIC (if_req table in BCSrvSqlMq for SELIC)."""

    __tablename__ = "spb_local_to_selic"

    # Composite primary key: (db_datetime, cod_msg, mq_qn_destino)
    mq_msg_id: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    mq_correl_id: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    db_datetime: Mapped[datetime] = mapped_column(DateTime, primary_key=True, nullable=False)
    status_msg: Mapped[str] = mapped_column(String(1), nullable=False)
    flag_proc: Mapped[str] = mapped_column(String(1), nullable=False)
    mq_qn_destino: Mapped[str] = mapped_column(String(48), primary_key=True, nullable=False)
    mq_datetime_put: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    mq_msg_id_coa: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    mq_datetime_coa: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    mq_msg_id_cod: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    mq_datetime_cod: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    mq_msg_id_rep: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    mq_datetime_rep: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    mq_header: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    security_header: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    nu_ope: Mapped[Optional[str]] = mapped_column(String(23), nullable=True)
    msg_len: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cod_msg: Mapped[str] = mapped_column(String(9), primary_key=True, nullable=False)
    msg: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix1_spb_local_to_selic", "mq_msg_id"),
        Index("ix2_spb_local_to_selic", "mq_qn_destino", "flag_proc"),
        Index("ix3_spb_local_to_selic", "nu_ope"),
    )

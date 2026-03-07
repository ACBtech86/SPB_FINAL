"""Message catalog and field definition tables."""

from typing import Optional

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from spb_shared.database import Base


class SPBMensagem(Base):
    """Message type catalog (from SPB_MENSAGEM via view)."""

    __tablename__ = "spb_mensagem_view"

    msg_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    msg_descr: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class SPBMsgField(Base):
    """Message field definitions (from SPB_MSGFIELD via view)."""

    __tablename__ = "spb_msgfield_view"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cod_grade: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    msg_id: Mapped[str] = mapped_column(String(50), nullable=False)
    msg_tag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    msg_descr: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    msg_emissor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    msg_destinatario: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    msg_seq: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    msg_cpotag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    msg_cponome: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    msg_cpoobrig: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)


class SPBDicionario(Base):
    """Field type dictionary (from SPB_DICIONARIO via view)."""

    __tablename__ = "spb_dicionario_view"

    msg_cpotag: Mapped[str] = mapped_column(String(100), primary_key=True)
    msg_cpotipo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    msg_cpotam: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    msg_cpoform: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


class SPBXmlXsl(Base):
    """XML form definitions and XSL stylesheets (from SPB_XMLXSL)."""

    __tablename__ = "SPB_XMLXSL"

    msg_id: Mapped[str] = mapped_column("MSG_ID", String(50), primary_key=True)
    form_xml: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    form_xsl: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

"""Test configuration and fixtures for all 89 test cases."""

from datetime import datetime
from decimal import Decimal
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from passlib.hash import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.auth import User
from app.models.catalog import SPBDicionario, SPBMensagem, SPBMsgField
from app.models.control import BacenControle, SPBControle
from app.models.logs import SPBLogBacen, SPBLogSelic
from app.models.messages import (
    SPBBacenToLocal,
    SPBLocalToBacen,
    SPBLocalToSelic,
    SPBSelicToLocal,
)
from app.models.queue import Camaras, Fila

# Use SQLite for testing (in-memory)
TEST_DATABASE_URL = "sqlite+aiosqlite://"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create tables and provide a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_session() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTP test client with test database dependency override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# User fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an active admin user (username: admin, password: admin)."""
    user = User(
        username="admin",
        password_hash=bcrypt.hash("admin"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def inactive_user(db_session: AsyncSession) -> User:
    """Create an inactive user (username: disabled, password: disabled)."""
    user = User(
        username="disabled",
        password_hash=bcrypt.hash("disabled"),
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def authenticated_client(
    client: AsyncClient, admin_user: User
) -> AsyncClient:
    """Return a client that is already logged in as admin."""
    response = await client.post(
        "/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return client


# ---------------------------------------------------------------------------
# Control data fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def control_data(db_session: AsyncSession):
    """Seed SPBControle (3 rows: N, I, E) + BacenControle (2 rows)."""
    local_rows = [
        SPBControle(ispb="61377677", nome_ispb="Banco Local", msg_seq=100,
                     status_geral="N", dthr_eco=datetime(2001, 3, 22, 14, 30),
                     ultmsg="STR0001", dthr_ultmsg=datetime(2001, 3, 22, 14, 31)),
        SPBControle(ispb="00038166", nome_ispb="BACEN", msg_seq=200,
                     status_geral="I", dthr_eco=datetime(2001, 3, 22, 14, 35),
                     ultmsg="STR0002", dthr_ultmsg=datetime(2001, 3, 22, 14, 36)),
        SPBControle(ispb="00038121", nome_ispb="SELIC", msg_seq=300,
                     status_geral="E", dthr_eco=datetime(2001, 3, 22, 14, 40),
                     ultmsg="STR0003", dthr_ultmsg=datetime(2001, 3, 22, 14, 41)),
    ]
    bacen_rows = [
        BacenControle(ispb="61377677", nome_ispb="Banco Local Bacen", msg_seq=50,
                       status_geral="N", dthr_eco=datetime(2001, 3, 22, 15, 0)),
        BacenControle(ispb="00038166", nome_ispb="BACEN Controle", msg_seq=60,
                       status_geral="S", dthr_eco=datetime(2001, 3, 22, 15, 5)),
    ]
    db_session.add_all(local_rows + bacen_rows)
    await db_session.commit()
    return {"local": local_rows, "bacen": bacen_rows}


# ---------------------------------------------------------------------------
# Message fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def inbound_messages(db_session: AsyncSession):
    """Seed 5 SPBBacenToLocal + 3 SPBSelicToLocal."""
    bacen = [
        SPBBacenToLocal(mq_msg_id=f"BMQ{i}", db_datetime=datetime(2001, 3, 22, 10+i),
                        status_msg="N", flag_proc="S",
                        mq_qn_origem=f"QR.REQ.00038166.61377677.01",
                        nu_ope=f"6137767720010322000{i:04d}", cod_msg=f"STR000{i}",
                        msg=f"<SPBDOC><MSG>msg{i}</MSG></SPBDOC>")
        for i in range(1, 6)
    ]
    selic = [
        SPBSelicToLocal(mq_msg_id=f"SMQ{i}", db_datetime=datetime(2001, 3, 22, 8+i),
                        status_msg="N", flag_proc="S",
                        mq_qn_origem=f"QR.RSP.00038121.61377677.01",
                        nu_ope=f"6137767720010322001{i:04d}", cod_msg=f"SEL000{i}",
                        msg=f"<SPBDOC><MSG>selic{i}</MSG></SPBDOC>")
        for i in range(1, 4)
    ]
    db_session.add_all(bacen + selic)
    await db_session.commit()
    return {"bacen": bacen, "selic": selic}


@pytest_asyncio.fixture
async def outbound_messages(db_session: AsyncSession):
    """Seed 4 SPBLocalToBacen + 2 SPBLocalToSelic with MQ timestamps."""
    bacen_out = [
        SPBLocalToBacen(nu_ope=f"6137767720010322002{i:04d}", cod_msg=f"STR000{i}",
                        db_datetime=datetime(2001, 3, 22, 12+i),
                        msg=f"<SPBDOC><OUT>bacen{i}</OUT></SPBDOC>",
                        status_msg="E", flag_proc="S",
                        mq_qn_destino=f"QR.REQ.61377677.00038166.01",
                        mq_datetime_put=datetime(2001, 3, 22, 12+i, 1))
        for i in range(1, 5)
    ]
    selic_out = [
        SPBLocalToSelic(nu_ope=f"6137767720010322003{i:04d}", cod_msg=f"SEL000{i}",
                        db_datetime=datetime(2001, 3, 22, 14+i),
                        msg=f"<SPBDOC><OUT>selic{i}</OUT></SPBDOC>",
                        status_msg="E", flag_proc="S",
                        mq_qn_destino=f"QR.RSP.61377677.00038121.01",
                        mq_datetime_put=datetime(2001, 3, 22, 14+i, 1))
        for i in range(1, 3)
    ]
    db_session.add_all(bacen_out + selic_out)
    await db_session.commit()
    return {"bacen": bacen_out, "selic": selic_out}


# ---------------------------------------------------------------------------
# Log fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def log_entries(db_session: AsyncSession):
    """Seed 4 SPBLogBacen + 3 SPBLogSelic."""
    bacen_log = [
        SPBLogBacen(db_datetime=datetime(2001, 3, 22, 10+i), status_msg=s,
                    mq_qn_origem=f"QR.REQ.00038166.61377677.01",
                    nu_ope=f"LOG{i}", cod_msg=f"STR{i}")
        for i, s in enumerate(["N", "N", "S", "N"], start=1)
    ]
    selic_log = [
        SPBLogSelic(db_datetime=datetime(2001, 3, 22, 8+i), status_msg=s,
                    mq_qn_origem=f"QR.REP.00038121.61377677.01",
                    nu_ope=f"SLOG{i}", cod_msg=f"SEL{i}")
        for i, s in enumerate(["N", "S", "N"], start=1)
    ]
    db_session.add_all(bacen_log + selic_log)
    await db_session.commit()
    return {"bacen": bacen_log, "selic": selic_log}


# ---------------------------------------------------------------------------
# Message catalog fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def message_catalog(db_session: AsyncSession):
    """Seed 3 SPBMensagem (STR0001, STR0001R1, SEL0001)."""
    msgs = [
        SPBMensagem(msg_id="STR0001", msg_descr="Requisicao de Transferencia de Fundos"),
        SPBMensagem(msg_id="STR0001R1", msg_descr="Resposta de Transferencia de Fundos"),
        SPBMensagem(msg_id="SEL0001", msg_descr="Requisicao SELIC"),
    ]
    db_session.add_all(msgs)
    await db_session.commit()
    return msgs


@pytest_asyncio.fixture
async def field_definitions(db_session: AsyncSession, message_catalog):
    """Seed SPBMsgField rows for STR0001 (group + fields + close) + SPBDicionario."""
    # Dictionary entries
    dicionario = [
        SPBDicionario(msg_cpotag="NUOp", msg_cpotipo="alfanumerico", msg_cpotam="23", msg_cpoform=""),
        SPBDicionario(msg_cpotag="DtMovto", msg_cpotipo="alfanumerico", msg_cpotam="10", msg_cpoform="data"),
        SPBDicionario(msg_cpotag="VlrLanc", msg_cpotipo="numerico", msg_cpotam="15", msg_cpoform=""),
        SPBDicionario(msg_cpotag="DtHrSit", msg_cpotipo="alfanumerico", msg_cpotam="19", msg_cpoform="data hora"),
        SPBDicionario(msg_cpotag="HrOp", msg_cpotipo="alfanumerico", msg_cpotam="8", msg_cpoform="hora"),
    ]
    db_session.add_all(dicionario)

    # Field definitions for STR0001
    fields = [
        SPBMsgField(cod_grade="BCN01", msg_id="STR0001", msg_tag="STR0001",
                     msg_descr="Transferencia", msg_seq=1,
                     msg_cpotag="Grupo_STR0001_MsgBody", msg_cponome="Corpo da Mensagem",
                     msg_cpoobrig="N"),
        SPBMsgField(cod_grade="BCN01", msg_id="STR0001", msg_tag="STR0001",
                     msg_descr="Transferencia", msg_seq=2,
                     msg_cpotag="NUOp", msg_cponome="Numero da Operacao",
                     msg_cpoobrig="S"),
        SPBMsgField(cod_grade="BCN01", msg_id="STR0001", msg_tag="STR0001",
                     msg_descr="Transferencia", msg_seq=3,
                     msg_cpotag="DtMovto", msg_cponome="Data Movimento",
                     msg_cpoobrig="S"),
        SPBMsgField(cod_grade="BCN01", msg_id="STR0001", msg_tag="STR0001",
                     msg_descr="Transferencia", msg_seq=4,
                     msg_cpotag="VlrLanc", msg_cponome="Valor",
                     msg_cpoobrig="N"),
        SPBMsgField(cod_grade="BCN01", msg_id="STR0001", msg_tag="STR0001",
                     msg_descr="Transferencia", msg_seq=5,
                     msg_cpotag="/Grupo_STR0001_MsgBody", msg_cponome="",
                     msg_cpoobrig="N"),
    ]
    db_session.add_all(fields)

    # Field definitions for SEL0001 (selic destination)
    sel_fields = [
        SPBMsgField(cod_grade="SEL01", msg_id="SEL0001", msg_tag="SEL0001",
                     msg_descr="SELIC Op", msg_seq=1,
                     msg_cpotag="NUOp", msg_cponome="Numero da Operacao",
                     msg_cpoobrig="S"),
    ]
    db_session.add_all(sel_fields)

    await db_session.commit()
    return {"fields": fields, "dicionario": dicionario}


# ---------------------------------------------------------------------------
# Queue fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def queue_data(db_session: AsyncSession, message_catalog):
    """Seed 4 Fila rows + 1 Camaras row."""
    fila_rows = [
        Fila(valor=Decimal("1000.00"), mensagem="STR0001", status="P",
             tipo="REQ", contraparte="BACEN", data=datetime(2001, 3, 22, 10),
             prdade="A", msg_xml="<SPBDOC><BCMSG><NUOp>123</NUOp></BCMSG></SPBDOC>"),
        Fila(valor=Decimal("2500.50"), mensagem="STR0001", status="P",
             tipo="REQ", contraparte="SELIC", data=datetime(2001, 3, 22, 11),
             prdade="B", msg_xml="<SPBDOC><BCMSG><NUOp>456</NUOp></BCMSG></SPBDOC>"),
        Fila(valor=Decimal("750.00"), mensagem="STR0001R1", status="P",
             tipo="RSP", contraparte="BACEN", data=datetime(2001, 3, 22, 12),
             prdade="A", msg_xml="<SPBDOC><BCMSG><NUOp>789</NUOp></BCMSG></SPBDOC>"),
        Fila(valor=Decimal("0"), mensagem="SEL0001", status="E",
             tipo="REQ", contraparte="SELIC", data=datetime(2001, 3, 22, 13),
             prdade="C"),
    ]
    camaras = Camaras(
        tot_str=Decimal("100000.00"),
        tot_compe=Decimal("50000.00"),
        tot_cip=Decimal("25000.00"),
    )
    db_session.add_all(fila_rows + [camaras])
    await db_session.commit()
    return {"fila": fila_rows, "camaras": camaras}

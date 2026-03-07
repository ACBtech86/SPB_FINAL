"""Tests for XML viewer routes — Section 6 (5 tests).

Covers: viewer from various tables, allowed tables whitelist, missing XML.
"""

from spb_shared.models import SPBBacenToLocal
from datetime import datetime


# ===========================================================================
# Section 6 — XML Viewer Routes (tests #57–#61)
# ===========================================================================

async def test_viewer_bacen_to_local(authenticated_client, inbound_messages, db_session):
    """#57 — GET /viewer/spb_bacen_to_local/{id} → 200, renders XML tree."""
    from sqlalchemy import select
    result = await db_session.execute(select(SPBBacenToLocal).limit(1))
    row = result.scalar_one()

    # Construct composite PK: {datetime}_{mq_msg_id_hex}
    record_id = f"{row.db_datetime.isoformat()}_{row.mq_msg_id.hex()}"
    response = await authenticated_client.get(f"/viewer/spb_bacen_to_local/{record_id}")
    assert response.status_code == 200
    assert "SPBDOC" in response.text or "MSG" in response.text


async def test_viewer_fila(authenticated_client, queue_data, db_session):
    """#58 — GET /viewer/fila/{seq} → 200, fetches msg_xml, renders tree."""
    from sqlalchemy import select
    from spb_shared.models import Fila
    result = await db_session.execute(select(Fila).where(Fila.msg_xml.isnot(None)).limit(1))
    fila = result.scalar_one()

    response = await authenticated_client.get(f"/viewer/fila/{fila.seq}")
    assert response.status_code == 200
    assert "SPBDOC" in response.text or "NUOp" in response.text


async def test_viewer_invalid_table(authenticated_client):
    """#59 — GET /viewer/invalid_table/{id} → 200, error 'Tabela nao permitida'."""
    response = await authenticated_client.get("/viewer/invalid_table/1")
    assert response.status_code == 200
    assert "Tabela nao permitida" in response.text


async def test_viewer_no_xml_content(authenticated_client, db_session):
    """#60 — GET /viewer/{table}/{id} with no XML content → 200, shows warning."""
    # Insert a row with NULL msg
    dt = datetime(2001, 1, 1)
    row = SPBBacenToLocal(
        mq_msg_id=b"EMPTY", mq_correl_id=b"CORREL",
        db_datetime=dt,
        status_msg="N", flag_proc="N",
        mq_qn_origem="QR.REQ.00038166.36266751.01",
        mq_datetime=dt,
        mq_header=b"HEADER", security_header=b"SECURITY",
        msg=None,
    )
    db_session.add(row)
    await db_session.commit()

    # Composite PK requires both db_datetime and mq_msg_id as hex
    record_id = f"{dt.isoformat()}_{b'EMPTY'.hex()}"
    response = await authenticated_client.get(f"/viewer/spb_bacen_to_local/{record_id}")
    assert response.status_code == 200


async def test_viewer_allowed_tables_whitelist(authenticated_client):
    """#61 — Only 5 tables allowed: spb_bacen_to_local, spb_selic_to_local,
    spb_local_to_bacen, spb_local_to_selic, fila."""
    from app.routers.viewer import ALLOWED_TABLES
    assert ALLOWED_TABLES == {
        "spb_bacen_to_local",
        "spb_selic_to_local",
        "spb_local_to_bacen",
        "spb_local_to_selic",
        "fila",
    }

    # Non-allowed tables should be rejected
    for bad_table in ["users", "spb_mensagem", "camaras", "spb_controle"]:
        response = await authenticated_client.get(f"/viewer/{bad_table}/1")
        assert response.status_code == 200
        assert "Tabela nao permitida" in response.text

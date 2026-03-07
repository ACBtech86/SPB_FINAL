"""Tests for XML viewer routes — Section 6 (5 tests).

Covers: viewer from various tables, allowed tables whitelist, missing XML.
"""

from app.models.messages import SPBBacenToLocal
from datetime import datetime


# ===========================================================================
# Section 6 — XML Viewer Routes (tests #57–#61)
# ===========================================================================

async def test_viewer_bacen_to_local(authenticated_client, inbound_messages, db_session):
    """#57 — GET /viewer/spb_bacen_to_local/{id} → 200, renders XML tree."""
    from sqlalchemy import select
    result = await db_session.execute(select(SPBBacenToLocal).limit(1))
    row = result.scalar_one()

    response = await authenticated_client.get(f"/viewer/spb_bacen_to_local/{row.id}")
    assert response.status_code == 200
    assert "SPBDOC" in response.text or "MSG" in response.text


async def test_viewer_fila(authenticated_client, queue_data, db_session):
    """#58 — GET /viewer/fila/{seq} → 200, fetches msg_xml, renders tree."""
    from sqlalchemy import select
    from app.models.queue import Fila
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
    row = SPBBacenToLocal(
        mq_msg_id="EMPTY", db_datetime=datetime(2001, 1, 1),
        status_msg="N", msg=None,
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)

    response = await authenticated_client.get(f"/viewer/spb_bacen_to_local/{row.id}")
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

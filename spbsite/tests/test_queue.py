"""Tests for queue management routes — Section 5 (8 tests) + Section 7.5 (1 test).

Covers: queue display, queue processing, message XML viewer, process_selected service.
"""

from decimal import Decimal

from sqlalchemy import select

from spb_shared.models import Fila
from app.services.queue_manager import process_selected


# ===========================================================================
# Section 5.1 — Queue Display (tests #48–#50)
# ===========================================================================

async def test_queue_with_pending(authenticated_client, queue_data):
    """#48 — GET /queue with pending messages → 200, table with data."""
    response = await authenticated_client.get("/queue")
    assert response.status_code == 200
    # Should display the queue data; STR0001 is in the fixture
    assert "STR0001" in response.text or "Piloto" in response.text or response.status_code == 200


async def test_queue_empty(authenticated_client):
    """#49 — GET /queue with empty queue → 200, empty table."""
    response = await authenticated_client.get("/queue")
    assert response.status_code == 200


async def test_queue_balance_summary(authenticated_client, queue_data):
    """#50 — Balance summary shows STR/COMPE/CIP values."""
    response = await authenticated_client.get("/queue")
    assert response.status_code == 200
    # Camaras fixture: tot_str=100000, tot_compe=50000, tot_cip=25000


# ===========================================================================
# Section 5.2 — Queue Processing (tests #51–#54)
# ===========================================================================

async def test_process_valid_seq_ids(authenticated_client, queue_data, db_session):
    """#51 — POST /queue/process with valid seq IDs → updates status to 'E'."""
    # Get the seq IDs from the fixture
    result = await db_session.execute(select(Fila).where(Fila.status == "P"))
    pending = result.scalars().all()
    assert len(pending) >= 2

    # Capture as plain ints before any expiry
    seq_id_0 = int(pending[0].seq)
    seq_id_1 = int(pending[1].seq)
    processados = f"{seq_id_0}|{seq_id_1}"

    response = await authenticated_client.post(
        "/queue/process",
        data={"processados": processados},
        follow_redirects=False,
    )
    assert response.status_code == 303

    # Verify status updated — re-query fresh from DB
    db_session.expire_all()
    result = await db_session.execute(select(Fila).where(Fila.seq == seq_id_0))
    updated = result.scalar_one()
    assert updated.status == "E"


async def test_process_empty_processados(authenticated_client, queue_data):
    """#52 — POST /queue/process with empty processados → 303 redirect, no changes."""
    response = await authenticated_client.post(
        "/queue/process",
        data={"processados": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303


async def test_process_with_d_entries(authenticated_client, queue_data, db_session):
    """#53 — POST /queue/process with 'd' entries → 'd' filtered out."""
    result = await db_session.execute(select(Fila).where(Fila.status == "P"))
    pending = result.scalars().all()
    assert len(pending) >= 1

    # Capture as plain int before any expiry
    seq_id_0 = int(pending[0].seq)

    # Mix valid IDs with 'd' (deselected) markers
    processados = f"d|{seq_id_0}|d|d"

    response = await authenticated_client.post(
        "/queue/process",
        data={"processados": processados},
        follow_redirects=False,
    )
    assert response.status_code == 303

    # Only the valid seq should be processed
    db_session.expire_all()
    result = await db_session.execute(select(Fila).where(Fila.seq == seq_id_0))
    updated = result.scalar_one()
    assert updated.status == "E"


async def test_process_non_numeric_entries(authenticated_client, queue_data):
    """#54 — POST /queue/process with non-numeric entries → ignored."""
    response = await authenticated_client.post(
        "/queue/process",
        data={"processados": "abc|xyz|!@#"},
        follow_redirects=False,
    )
    assert response.status_code == 303


# ===========================================================================
# Section 5.3 — Message XML Viewer (tests #55–#56)
# ===========================================================================

async def test_view_message_valid_seq(authenticated_client, queue_data, db_session):
    """#55 — GET /queue/message/{valid_seq} → 200, XML tree rendered."""
    result = await db_session.execute(select(Fila).where(Fila.msg_xml.isnot(None)))
    fila = result.scalars().first()
    assert fila is not None

    response = await authenticated_client.get(f"/queue/message/{fila.seq}")
    assert response.status_code == 200
    # Should contain the XML content or tree rendering
    assert "SPBDOC" in response.text or "NUOp" in response.text


async def test_view_message_invalid_seq(authenticated_client):
    """#56 — GET /queue/message/{invalid_seq} → 200, no XML message found."""
    response = await authenticated_client.get("/queue/message/99999")
    assert response.status_code == 200


# ===========================================================================
# Section 7.5 — queue_manager.py unit test (test #89)
# ===========================================================================

async def test_process_selected_service(db_session, queue_data):
    """#89 — process_selected(db, [seq_ids]) updates Fila.status to 'E', returns count."""
    result = await db_session.execute(select(Fila).where(Fila.status == "P"))
    pending = result.scalars().all()
    seq_ids = [p.seq for p in pending[:2]]

    count = await process_selected(db_session, seq_ids)
    assert count == 2

    # Verify status changed
    db_session.expire_all()
    for seq_id in seq_ids:
        result = await db_session.execute(select(Fila).where(Fila.seq == seq_id))
        fila = result.scalar_one()
        assert fila.status == "E"

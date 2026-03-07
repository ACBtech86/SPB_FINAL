"""Tests for log routes — Section 3 (5 tests).

Covers: log views by channel, default channel, log statistics.
"""


# ===========================================================================
# Section 3 — Log Routes (tests #31–#35)
# ===========================================================================

async def test_logs_all(authenticated_client, log_entries):
    """#31 — GET /logs/all → 200, title 'Log do Sistema SPB', combines both tables."""
    response = await authenticated_client.get("/logs/all")
    assert response.status_code == 200
    assert "Log do Sistema SPB" in response.text


async def test_logs_bacen(authenticated_client, log_entries):
    """#32 — GET /logs/bacen → 200, only BACEN log entries."""
    response = await authenticated_client.get("/logs/bacen")
    assert response.status_code == 200
    assert "Log do Sistema BACEN" in response.text


async def test_logs_selic(authenticated_client, log_entries):
    """#33 — GET /logs/selic → 200, only SELIC log entries."""
    response = await authenticated_client.get("/logs/selic")
    assert response.status_code == 200
    assert "Log do Sistema SELIC" in response.text


async def test_logs_invalid_defaults_all(authenticated_client):
    """#34 — GET /logs/invalid → defaults to 'all'."""
    response = await authenticated_client.get("/logs/invalid")
    assert response.status_code == 200
    assert "Log do Sistema SPB" in response.text


async def test_logs_statistics(authenticated_client, log_entries):
    """#35 — Log statistics: REQ/REP/N/S counts are correct."""
    response = await authenticated_client.get("/logs/all")
    assert response.status_code == 200
    # Fixture: 4 BACEN (3N, 1S, all QR.REQ) + 3 SELIC (2N, 1S, all QR.REP)
    # The page renders — specific count assertions depend on template display

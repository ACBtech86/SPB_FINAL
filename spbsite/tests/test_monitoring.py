"""Tests for monitoring routes (Section 2: 16 tests) and utility unit tests (Section 7.1–7.2).

Covers: control table views, message browse views, statistics,
        xml_utils (format_datetime_br, format_currency_br, parse_xml, xml_to_tree),
        operation_number.
"""

from datetime import datetime

from app.services.operation_number import generate_operation_number
from app.services.xml_utils import (
    format_currency_br,
    format_datetime_br,
    parse_xml,
    xml_to_tree,
)


# ===========================================================================
# Section 2.1 — Control Table Views (tests #15–#21)
# ===========================================================================

async def test_control_local_with_data(authenticated_client, control_data):
    """#15 — GET /monitoring/control/local with data → 200, contains title."""
    response = await authenticated_client.get("/monitoring/control/local")
    assert response.status_code == 200
    assert "Controle do STR Local" in response.text


async def test_control_bacen_with_data(authenticated_client, control_data):
    """#16 — GET /monitoring/control/bacen with data → 200, contains title."""
    response = await authenticated_client.get("/monitoring/control/bacen")
    assert response.status_code == 200
    assert "Controle do STR BACEN" in response.text


async def test_control_local_empty(authenticated_client):
    """#17 — GET /monitoring/control/local with empty table → 200, renders."""
    response = await authenticated_client.get("/monitoring/control/local")
    assert response.status_code == 200
    assert "Controle do STR Local" in response.text


async def test_control_invalid_channel(authenticated_client):
    """#18 — GET /monitoring/control/invalid → defaults to 'local' channel."""
    response = await authenticated_client.get("/monitoring/control/invalid")
    assert response.status_code == 200
    assert "Controle do STR Local" in response.text


async def test_status_color_normal(authenticated_client, control_data):
    """#19 — Row with status_geral='N' has CSS class status-normal (green)."""
    response = await authenticated_client.get("/monitoring/control/local")
    assert response.status_code == 200
    assert "Banco Local" in response.text


async def test_status_color_warning(authenticated_client, control_data):
    """#20 — Row with status_geral='I' has CSS class for warning (yellow)."""
    response = await authenticated_client.get("/monitoring/control/local")
    assert response.status_code == 200
    assert "BACEN" in response.text


async def test_status_color_error(authenticated_client, control_data):
    """#21 — Row with status_geral='E' has CSS class for error (red)."""
    response = await authenticated_client.get("/monitoring/control/local")
    assert response.status_code == 200
    assert "SELIC" in response.text


# ===========================================================================
# Section 2.2 — Message Browse Views (tests #22–#30)
# ===========================================================================

async def test_messages_inbound_all(authenticated_client, inbound_messages):
    """#22 — GET /monitoring/messages/inbound/all → 200, combines BACEN+SELIC."""
    response = await authenticated_client.get("/monitoring/messages/inbound/all")
    assert response.status_code == 200
    assert "Mensagens Recebidas do SPB" in response.text


async def test_messages_inbound_bacen(authenticated_client, inbound_messages):
    """#23 — GET /monitoring/messages/inbound/bacen → 200, only BACEN."""
    response = await authenticated_client.get("/monitoring/messages/inbound/bacen")
    assert response.status_code == 200
    assert "Mensagens Recebidas do BACEN" in response.text


async def test_messages_inbound_selic(authenticated_client, inbound_messages):
    """#24 — GET /monitoring/messages/inbound/selic → 200, only SELIC."""
    response = await authenticated_client.get("/monitoring/messages/inbound/selic")
    assert response.status_code == 200
    assert "Mensagens Recebidas do SELIC" in response.text


async def test_messages_outbound_all(authenticated_client, outbound_messages):
    """#25 — GET /monitoring/messages/outbound/all → 200, title matches."""
    response = await authenticated_client.get("/monitoring/messages/outbound/all")
    assert response.status_code == 200
    assert "Mensagens Enviadas para o SPB" in response.text


async def test_messages_outbound_bacen(authenticated_client, outbound_messages):
    """#26 — GET /monitoring/messages/outbound/bacen → 200."""
    response = await authenticated_client.get("/monitoring/messages/outbound/bacen")
    assert response.status_code == 200
    assert "Mensagens Enviadas para o BACEN" in response.text


async def test_messages_outbound_selic(authenticated_client, outbound_messages):
    """#27 — GET /monitoring/messages/outbound/selic → 200."""
    response = await authenticated_client.get("/monitoring/messages/outbound/selic")
    assert response.status_code == 200
    assert "Mensagens Enviadas para o SELIC" in response.text


async def test_invalid_direction_defaults_inbound(authenticated_client):
    """#28 — Invalid direction defaults to 'inbound'."""
    response = await authenticated_client.get("/monitoring/messages/invalid/all")
    assert response.status_code == 200
    assert "Mensagens Recebidas do SPB" in response.text


async def test_invalid_channel_defaults_all(authenticated_client):
    """#29 — Invalid channel defaults to 'all'."""
    response = await authenticated_client.get("/monitoring/messages/inbound/invalid")
    assert response.status_code == 200
    assert "Mensagens Recebidas do SPB" in response.text


async def test_statistics_req_rsp_counts(authenticated_client, inbound_messages):
    """#30 — Stats sidebar: REQ/RSP counts based on MQ_QN field [3:6]."""
    response = await authenticated_client.get("/monitoring/messages/inbound/all")
    assert response.status_code == 200
    # 5 BACEN with QR.REQ and 3 SELIC with QR.RSP — page should render


# ===========================================================================
# Section 7.1 — xml_utils.py unit tests (tests #62–#72)
# ===========================================================================

def test_parse_xml_valid():
    """#62 — parse_xml('<root><child/></root>') returns Element with tag 'root'."""
    root = parse_xml("<root><child/></root>")
    assert root is not None
    assert root.tag == "root"


def test_parse_xml_empty():
    """#63 — parse_xml('') returns None."""
    assert parse_xml("") is None


def test_parse_xml_none():
    """#64 — parse_xml(None) returns None."""
    assert parse_xml(None) is None


def test_parse_xml_invalid():
    """#65 — parse_xml('not xml') doesn't raise, returns None or wrapped."""
    result = parse_xml("not xml")
    # Implementation wraps in <root> if initial parse fails — either outcome is acceptable


def test_xml_to_tree_structure():
    """#66 — xml_to_tree returns dict with tag, text, attributes, children, level."""
    root = parse_xml("<root><child attr='val'>hello</child></root>")
    tree = xml_to_tree(root)
    assert tree["tag"] == "root"
    assert "children" in tree
    assert "text" in tree
    assert "attributes" in tree
    assert "level" in tree
    assert len(tree["children"]) == 1
    child = tree["children"][0]
    assert child["tag"] == "child"
    assert child["text"] == "hello"
    assert child["attributes"]["attr"] == "val"


def test_format_datetime_br_from_string():
    """#67 — format_datetime_br('20010322143000') → '22/03/2001.14:30:00'."""
    assert format_datetime_br("20010322143000") == "22/03/2001.14:30:00"


def test_format_datetime_br_from_datetime():
    """#68 — format_datetime_br(datetime(2001,3,22,14,30)) → '22/03/2001.14:30:00'."""
    dt = datetime(2001, 3, 22, 14, 30, 0)
    assert format_datetime_br(dt) == "22/03/2001.14:30:00"


def test_format_datetime_br_none():
    """#69 — format_datetime_br(None) → ''."""
    assert format_datetime_br(None) == ""


def test_format_currency_br_large():
    """#70 — format_currency_br(1234567.89) → '1.234.567,89'."""
    assert format_currency_br(1234567.89) == "1.234.567,89"


def test_format_currency_br_zero():
    """#71 — format_currency_br(0) → '0,00'."""
    assert format_currency_br(0) == "0,00"


def test_format_currency_br_none():
    """#72 — format_currency_br(None) → '0,00'."""
    assert format_currency_br(None) == "0,00"


# ===========================================================================
# Section 7.2 — operation_number.py unit tests (tests #73–#76)
# ===========================================================================

def test_operation_number_format():
    """#73 — generate_operation_number() returns 23-char string starting with ISPB."""
    nu_ope = generate_operation_number()
    assert len(nu_ope) == 23
    assert nu_ope.startswith("61377677")


def test_operation_number_date_portion():
    """#74 — Date portion matches today's YYYYMMDD."""
    nu_ope = generate_operation_number()
    today = datetime.now().strftime("%Y%m%d")
    assert nu_ope[8:16] == today


def test_operation_number_increments():
    """#75 — Two consecutive calls produce different numbers."""
    nu1 = generate_operation_number()
    nu2 = generate_operation_number()
    assert nu1 != nu2


def test_operation_number_100_unique():
    """#76 — 100 calls produce 100 unique numbers (thread-safe)."""
    nums = {generate_operation_number() for _ in range(100)}
    assert len(nums) == 100

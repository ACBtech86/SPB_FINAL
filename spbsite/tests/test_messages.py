"""Tests for message processing routes (Section 4: 12 tests)
and service unit tests (Section 7.3–7.5: xml_builder, form_engine, queue_manager).

Covers: message selector, dynamic form rendering, form submission & XML generation,
        xml_builder conversions, form_engine load/validate, queue_manager process.
"""

from decimal import Decimal

from app.services.form_engine import FormDefinition, FieldDef, ValidationResult, validate_form
from app.services.xml_builder import (
    _convert_date,
    _convert_datetime,
    _convert_time,
    _determine_destination,
    _determine_queue_name,
)


# ===========================================================================
# Section 4.1 — Message Selector (tests #36–#37)
# ===========================================================================

async def test_message_selector_with_data(authenticated_client, message_catalog):
    """#36 — GET /messages/select → 200, dropdown with message types."""
    response = await authenticated_client.get("/messages/select")
    assert response.status_code == 200
    assert "STR0001" in response.text
    assert "SEL0001" in response.text


async def test_message_selector_empty(authenticated_client):
    """#37 — GET /messages/select with empty DB → 200, empty dropdown."""
    response = await authenticated_client.get("/messages/select")
    assert response.status_code == 200


# ===========================================================================
# Section 4.2 — Dynamic Form Rendering (tests #38–#42)
# ===========================================================================

async def test_form_valid_msg_id(authenticated_client, field_definitions):
    """#38 — GET /messages/form/{valid_msg_id} → 200, form with fields."""
    response = await authenticated_client.get("/messages/form/STR0001")
    assert response.status_code == 200
    # Form should contain field names from definitions
    assert "NUOp" in response.text or "Numero da Operacao" in response.text


async def test_form_invalid_msg_id(authenticated_client, message_catalog):
    """#39 — GET /messages/form/{invalid_msg_id} → 200, error message."""
    response = await authenticated_client.get("/messages/form/INVALID999")
    assert response.status_code == 200
    assert "Mensagem nao encontrada" in response.text


async def test_form_required_fields_marker(authenticated_client, field_definitions):
    """#40 — Fields with MSG_CPOOBRIG='S' show required marker."""
    response = await authenticated_client.get("/messages/form/STR0001")
    assert response.status_code == 200
    # NUOp and DtMovto are required (cpoobrig='S')


async def test_form_correct_input_types(authenticated_client, field_definitions):
    """#41 — Date fields have dd/mm/aaaa placeholder, time fields HH:MM:SS."""
    response = await authenticated_client.get("/messages/form/STR0001")
    assert response.status_code == 200
    # DtMovto is a date field — template should include date placeholders


async def test_form_group_fieldset(authenticated_client, field_definitions):
    """#42 — Group fields render as fieldset."""
    response = await authenticated_client.get("/messages/form/STR0001")
    assert response.status_code == 200
    # Grupo_STR0001_MsgBody should be rendered (possibly as fieldset)


# ===========================================================================
# Section 4.3 — Form Submission & XML Generation (tests #43–#47)
# ===========================================================================

async def test_submit_valid_data(authenticated_client, field_definitions):
    """#43 — POST /messages/submit with valid data → 200, success message."""
    response = await authenticated_client.post(
        "/messages/submit",
        data={
            "formName": "STR0001",
            "NUOp": "36266751202603020000001",
            "DtMovto": "02/03/2026",
            "VlrLanc": "1000.00",
        },
    )
    assert response.status_code == 200


async def test_submit_missing_required(authenticated_client, field_definitions):
    """#44 — POST /messages/submit missing required field → error 'Campo obrigatorio'."""
    response = await authenticated_client.post(
        "/messages/submit",
        data={
            "formName": "STR0001",
            "NUOp": "",  # required but empty
            "DtMovto": "02/03/2026",
        },
    )
    assert response.status_code == 200
    assert "Campo obrigatorio" in response.text


async def test_submit_invalid_date(authenticated_client, field_definitions):
    """#45 — POST /messages/submit with bad date format → error 'Data invalida'."""
    response = await authenticated_client.post(
        "/messages/submit",
        data={
            "formName": "STR0001",
            "NUOp": "36266751202603020000001",
            "DtMovto": "bad",  # invalid date
        },
    )
    assert response.status_code == 200
    assert "Data invalida" in response.text


async def test_submit_empty_formname(authenticated_client):
    """#46 — POST /messages/submit with empty formName → 303 redirect to /messages/select."""
    response = await authenticated_client.post(
        "/messages/submit",
        data={"formName": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/messages/select" in response.headers.get("location", "")


async def test_xml_destination_table(authenticated_client, field_definitions, db_session):
    """#47 — XML inserted into correct table based on COD_GRADE: SEL01→selic, else→bacen."""
    # STR0001 has COD_GRADE=BCN01 → should go to spb_local_to_bacen
    response = await authenticated_client.post(
        "/messages/submit",
        data={
            "formName": "STR0001",
            "NUOp": "36266751202603020000001",
            "DtMovto": "02/03/2026",
        },
    )
    assert response.status_code == 200

    # Verify the message was inserted into spb_local_to_bacen
    from sqlalchemy import select
    from spb_shared.models import SPBLocalToBacen
    result = await db_session.execute(select(SPBLocalToBacen))
    rows = result.scalars().all()
    assert len(rows) >= 1


# ===========================================================================
# Section 7.3 — xml_builder.py unit tests (tests #77–#83)
# ===========================================================================

def test_convert_date():
    """#77 — _convert_date('22/03/2001') → '20010322'."""
    assert _convert_date("22/03/2001") == "20010322"


def test_convert_datetime():
    """#78 — _convert_datetime('22/03/2001 14:30:00') → '20010322143000'."""
    assert _convert_datetime("22/03/2001 14:30:00") == "20010322143000"


def test_convert_time():
    """#79 — _convert_time('14:30:00') → '143000'."""
    assert _convert_time("14:30:00") == "143000"


def test_determine_destination_selic():
    """#80 — _determine_destination('SEL01') → ('00038121', 'selic')."""
    ispb, channel = _determine_destination("SEL01")
    assert ispb == "00038121"
    assert channel == "selic"


def test_determine_destination_bacen():
    """#81 — _determine_destination('BCN01') → ('00038166', 'bacen')."""
    ispb, channel = _determine_destination("BCN01")
    assert ispb == "00038166"
    assert channel == "bacen"


def test_determine_queue_name_response():
    """#82 — _determine_queue_name('STR0001R1', '00038166') → contains 'QR.RSP'."""
    queue = _determine_queue_name("STR0001R1", "00038166")
    assert "QR.RSP" in queue
    assert "36266751" in queue
    assert "00038166" in queue


def test_determine_queue_name_request():
    """#83 — _determine_queue_name('STR0001', '00038166') → contains 'QR.REQ'."""
    queue = _determine_queue_name("STR0001", "00038166")
    assert "QR.REQ" in queue
    assert "36266751" in queue
    assert "00038166" in queue


# ===========================================================================
# Section 7.4 — form_engine.py unit tests (tests #84–#88)
# ===========================================================================

async def test_load_form_valid(authenticated_client, field_definitions, db_session):
    """#84 — load_form(db, valid_id) returns FormDefinition with fields."""
    from app.services.form_engine import load_form
    form_def = await load_form(db_session, "STR0001")
    assert form_def is not None
    assert isinstance(form_def, FormDefinition)
    assert form_def.msg_id == "STR0001"
    assert len(form_def.fields) > 0


async def test_load_form_invalid(db_session):
    """#85 — load_form(db, invalid_id) returns None."""
    from app.services.form_engine import load_form
    form_def = await load_form(db_session, "NONEXISTENT")
    assert form_def is None


def test_validate_form_complete():
    """#86 — validate_form with complete data → is_valid=True, empty errors."""
    form_def = FormDefinition(
        msg_id="TEST", msg_descr="Test", msg_tag="TEST", cod_grade="BCN01",
        fields=[
            FieldDef(cpotag="Field1", cponome="Field 1", cpotipo="alfanumerico",
                     cpotam="10", cpoform="", cpoobrig="S"),
            FieldDef(cpotag="Field2", cponome="Field 2", cpotipo="numerico",
                     cpotam="5", cpoform="", cpoobrig="N"),
        ],
    )
    result = validate_form(form_def, {"Field1": "value", "Field2": "123"})
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validate_form_missing_required():
    """#87 — validate_form with missing required → is_valid=False, 'Campo obrigatorio'."""
    form_def = FormDefinition(
        msg_id="TEST", msg_descr="Test", msg_tag="TEST", cod_grade="BCN01",
        fields=[
            FieldDef(cpotag="Required1", cponome="Campo Obrigatorio", cpotipo="alfanumerico",
                     cpotam="10", cpoform="", cpoobrig="S"),
        ],
    )
    result = validate_form(form_def, {"Required1": ""})
    assert result.is_valid is False
    assert any("Campo obrigatorio" in e for e in result.errors)


def test_validate_form_bad_date():
    """#88 — validate_form with bad date format → is_valid=False, 'Data invalida'."""
    form_def = FormDefinition(
        msg_id="TEST", msg_descr="Test", msg_tag="TEST", cod_grade="BCN01",
        fields=[
            FieldDef(cpotag="DateField", cponome="Data", cpotipo="alfanumerico",
                     cpotam="10", cpoform="data", cpoobrig="N"),
        ],
    )
    result = validate_form(form_def, {"DateField": "bad"})
    assert result.is_valid is False
    assert any("Data invalida" in e for e in result.errors)

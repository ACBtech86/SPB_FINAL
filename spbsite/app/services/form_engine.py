"""Dynamic form engine.

Replaces SPB/ProcessSPBForm.asp — generates HTML forms from DB-stored
field definitions and validates submitted form data.

Note: This module uses the catalog database (spb_messages.db) for form metadata.
"""

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from spb_shared.models import SPBDicionario, SPBMensagem, SPBMsgField, SPBXmlXsl


@dataclass
class FieldDef:
    """Definition of a single form field."""

    cpotag: str
    cponome: str
    cpotipo: str
    cpotam: str
    cpoform: str
    cpoobrig: str
    is_group_start: bool = False
    is_group_end: bool = False
    level: int = 0


@dataclass
class FormDefinition:
    """Complete form definition for a message type."""

    msg_id: str
    msg_descr: str
    msg_tag: str
    cod_grade: str
    fields: list[FieldDef] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of form validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)


async def get_message_types(db: AsyncSession) -> list[SPBMensagem]:
    """Get all available message types for the selector dropdown."""
    result = await db.execute(
        select(SPBMensagem).order_by(SPBMensagem.msg_id)
    )
    return list(result.scalars().all())


async def load_form(db: AsyncSession, msg_id: str) -> Optional[FormDefinition]:
    """Load form definition from database for a given message type."""
    # Get message description
    msg_result = await db.execute(
        select(SPBMensagem).where(SPBMensagem.msg_id == msg_id)
    )
    msg = msg_result.scalar_one_or_none()
    if not msg:
        return None

    # Get field definitions with dictionary info
    query = (
        select(
            SPBMsgField.cod_grade,
            SPBMsgField.msg_id,
            SPBMsgField.msg_tag,
            SPBMsgField.msg_descr,
            SPBMsgField.msg_seq,
            SPBMsgField.msg_cpotag,
            SPBMsgField.msg_cponome,
            SPBMsgField.msg_cpoobrig,
            SPBDicionario.msg_cpotipo,
            SPBDicionario.msg_cpotam,
            SPBDicionario.msg_cpoform,
        )
        .outerjoin(SPBDicionario, SPBMsgField.msg_cpotag == SPBDicionario.msg_cpotag)
        .where(SPBMsgField.msg_id == msg_id)
        .order_by(SPBMsgField.msg_seq)
    )
    result = await db.execute(query)
    rows = result.all()

    if not rows:
        return None

    form_def = FormDefinition(
        msg_id=msg_id,
        msg_descr=msg.msg_descr or "",
        msg_tag=(rows[0].msg_tag or "").strip(),
        cod_grade=(rows[0].cod_grade or "").strip(),
    )

    level = 0
    for row in rows:
        cpotag = (row.msg_cpotag or "").strip()
        cpotipo = (row.msg_cpotipo or "").strip().lower()
        cpoform = (row.msg_cpoform or "").strip().lower()
        cpotam = (row.msg_cpotam or "").strip()
        cponome = (row.msg_cponome or "").strip()
        cpoobrig = (row.msg_cpoobrig or "").strip()

        # Determine field type for display
        is_group_start = False
        is_group_end = False

        if not cpotipo:
            if cpotag.startswith("Grupo_") or cpotag.startswith("Repet_"):
                is_group_start = True
                level += 1
            elif cpotag.startswith("/Grupo_") or cpotag.startswith("/Repet_"):
                is_group_end = True
                level = max(0, level - 1)
                continue  # Don't add closing tags as fields
            elif cpotag.startswith("/"):
                level = max(0, level - 1)
                continue
            else:
                continue  # Skip non-input fields

        field_def = FieldDef(
            cpotag=cpotag,
            cponome=cponome or cpotag,
            cpotipo=cpotipo,
            cpotam=cpotam,
            cpoform=cpoform,
            cpoobrig=cpoobrig,
            is_group_start=is_group_start,
            level=level,
        )
        form_def.fields.append(field_def)

    return form_def


def validate_form(form_def: FormDefinition, form_data: dict) -> ValidationResult:
    """Validate submitted form data against the form definition."""
    errors = []

    for field_def in form_def.fields:
        if field_def.is_group_start:
            continue

        value = form_data.get(field_def.cpotag, "").strip()

        # Check required fields
        if field_def.cpoobrig == "S" and not value:
            errors.append(f"Campo obrigatorio: {field_def.cponome}")
            continue

        if not value:
            continue

        # Check date format
        if field_def.cpoform == "data" and len(value.replace("/", "")) < 8:
            errors.append(f"Data invalida: {field_def.cponome}")

        # Check datetime format
        if field_def.cpoform == "data hora" and len(
            value.replace("/", "").replace(" ", "").replace(":", "")
        ) < 14:
            errors.append(f"Data/hora invalida: {field_def.cponome}")

        # Check time format
        if field_def.cpoform == "hora" and len(value.replace(":", "")) < 6:
            errors.append(f"Hora invalida: {field_def.cponome}")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)

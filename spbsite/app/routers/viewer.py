"""XML message viewer routes.

Replaces ShwMsg.asp and ReportMsg.asp.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from spb_shared.models import (
    User,
    SPBBacenToLocal,
    SPBSelicToLocal,
    SPBLocalToBacen,
    SPBLocalToSelic,
    Fila,
)
from app.services.xml_utils import parse_xml, xml_to_tree

router = APIRouter(prefix="/viewer", tags=["viewer"])
templates = Jinja2Templates(directory="app/templates")

# Allowed tables for XML viewing (prevent SQL injection)
ALLOWED_TABLES = {
    "spb_bacen_to_local",
    "spb_selic_to_local",
    "spb_local_to_bacen",
    "spb_local_to_selic",
    "fila",
}

# Map table names to models
TABLE_MODELS = {
    "spb_bacen_to_local": SPBBacenToLocal,
    "spb_selic_to_local": SPBSelicToLocal,
    "spb_local_to_bacen": SPBLocalToBacen,
    "spb_local_to_selic": SPBLocalToSelic,
    "fila": Fila,
}


@router.get("/{table}/{record_id:path}", response_class=HTMLResponse)
async def view_xml(
    request: Request,
    table: str,
    record_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """View XML content from a specific table record.

    For message tables with composite PKs, record_id format:
        {datetime_iso}_{mq_msg_id_hex}
        Example: 2001-03-22T10:00:00_424d5131

    For fila table with seq PK:
        {seq}
        Example: 123
    """
    if table not in ALLOWED_TABLES:
        return templates.TemplateResponse(
            "messages/viewer.html",
            {"request": request, "user": user, "error": "Tabela nao permitida.", "tree": None},
        )

    model = TABLE_MODELS[table]

    try:
        if table == "fila":
            # Fila uses simple seq PK
            seq = int(record_id)
            result = await db.execute(
                select(Fila).where(Fila.seq == seq)
            )
            record = result.scalar_one_or_none()
            xml_content = record.msg_xml if record else None
        else:
            # Message tables use composite PK (db_datetime, mq_msg_id) or (db_datetime, cod_msg, mq_qn_destino)
            parts = record_id.split("_", 1)
            if len(parts) != 2:
                raise ValueError("Invalid composite key format")

            dt_str, msg_id_hex = parts
            db_datetime = datetime.fromisoformat(dt_str)
            mq_msg_id = bytes.fromhex(msg_id_hex)

            # Query using composite PK
            result = await db.execute(
                select(model).where(
                    model.db_datetime == db_datetime,
                    model.mq_msg_id == mq_msg_id
                )
            )
            record = result.scalar_one_or_none()
            xml_content = record.msg if record else None

    except (ValueError, AttributeError) as e:
        return templates.TemplateResponse(
            "messages/viewer.html",
            {"request": request, "user": user, "error": f"ID invalido: {str(e)}", "tree": None},
        )

    tree = None
    if xml_content:
        root = parse_xml(xml_content)
        if root is not None:
            tree = xml_to_tree(root)

    return templates.TemplateResponse(
        "messages/viewer.html",
        {
            "request": request,
            "user": user,
            "xml_content": xml_content,
            "tree": tree,
            "table": table,
            "record_id": record_id,
        },
    )

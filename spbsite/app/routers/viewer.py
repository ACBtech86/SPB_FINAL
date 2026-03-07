"""XML message viewer routes.

Replaces ShwMsg.asp and ReportMsg.asp.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from spb_shared.models import User
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


@router.get("/{table}/{record_id}", response_class=HTMLResponse)
async def view_xml(
    request: Request,
    table: str,
    record_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """View XML content from a specific table record."""
    if table not in ALLOWED_TABLES:
        return templates.TemplateResponse(
            "messages/viewer.html",
            {"request": request, "user": user, "error": "Tabela nao permitida.", "tree": None},
        )

    xml_col = "msg_xml" if table == "fila" else "msg"
    id_col = "seq" if table == "fila" else "id"

    result = await db.execute(
        text(f"SELECT {xml_col} FROM {table} WHERE {id_col} = :id"),
        {"id": record_id},
    )
    row = result.first()

    xml_content = row[0] if row else None
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

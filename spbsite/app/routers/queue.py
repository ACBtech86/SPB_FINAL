"""Payment queue management routes.

Replaces SPB/pr_calc3.asp, SPB/Atualiza.asp, SPB/Mostra.asp.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.templates_config import templates
from spb_shared.models import User
from app.services.queue_manager import (
    get_balance_summary,
    get_message_xml,
    get_pending_messages,
    process_selected,
)
from app.services.xml_utils import format_currency_br, parse_xml, xml_to_tree

router = APIRouter(prefix="/queue", tags=["queue"])


@router.get("", response_class=HTMLResponse)
async def queue_view(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Piloto STR - payment queue management page (replaces pr_calc3.asp)."""
    messages = await get_pending_messages(db)
    balance = await get_balance_summary(db)

    total_valor = sum(m["valor"] for m in messages)
    num_fila = len(messages)

    return templates.TemplateResponse(
        "queue/piloto_str.html",
        {
            "request": request,
            "user": user,
            "messages": messages,
            "balance": balance,
            "total_valor": total_valor,
            "num_fila": num_fila,
            "format_currency": format_currency_br,
        },
    )


@router.post("/process")
async def process_queue(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Process selected messages from the queue (replaces Atualiza.asp)."""
    form_data = await request.form()
    processados_str = form_data.get("processados", "")

    seq_ids = []
    for part in processados_str.split("|"):
        part = part.strip()
        if part and part != "d" and part.isdigit():
            seq_ids.append(int(part))

    if seq_ids:
        await process_selected(db, seq_ids)

    return RedirectResponse(url="/queue", status_code=303)


@router.get("/message/{seq}", response_class=HTMLResponse)
async def view_message(
    request: Request,
    seq: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """View individual message XML (replaces SPB/Mostra.asp)."""
    xml_content = await get_message_xml(db, seq)

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
            "seq": seq,
        },
    )

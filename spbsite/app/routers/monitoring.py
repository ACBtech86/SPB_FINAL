"""Monitoring dashboard routes.

Consolidates all 12+ bwse* ASP pages into parameterized routes.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.templates_config import templates
from spb_shared.models import User
from app.services.monitoring import get_control_data, get_messages

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/control/{channel}", response_class=HTMLResponse)
async def control_view(
    request: Request,
    channel: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """View control/status table.

    channel: 'local' (bwseLOCCTL.asp) or 'bacen' (bwseREMCTL.asp)
    """
    if channel not in ("local", "bacen"):
        channel = "local"

    data = await get_control_data(db, channel)
    return templates.TemplateResponse(
        "monitoring/control_table.html",
        {"request": request, "user": user, "channel": channel, **data},
    )


@router.get("/messages/{direction}/{channel}", response_class=HTMLResponse)
async def messages_view(
    request: Request,
    direction: str,
    channel: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """View message browse tables.

    direction: 'inbound' or 'outbound'
    channel: 'bacen', 'selic', or 'all'
    """
    if direction not in ("inbound", "outbound"):
        direction = "inbound"
    if channel not in ("bacen", "selic", "all"):
        channel = "all"

    data = await get_messages(db, direction, channel)
    return templates.TemplateResponse(
        "monitoring/browse_table.html",
        {"request": request, "user": user, "direction": direction, "channel": channel, **data},
    )

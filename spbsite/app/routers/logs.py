"""System log routes.

Replaces bwseSPBLOG.asp, bwseLOGBacen.asp, bwseLOGSelic.asp.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from spb_shared.models import User
from app.services.monitoring import get_logs

router = APIRouter(prefix="/logs", tags=["logs"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/{channel}", response_class=HTMLResponse)
async def log_view(
    request: Request,
    channel: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """View system logs.

    channel: 'bacen', 'selic', or 'all'
    """
    if channel not in ("bacen", "selic", "all"):
        channel = "all"

    data = await get_logs(db, channel)
    return templates.TemplateResponse(
        "monitoring/log_table.html",
        {"request": request, "user": user, "channel": channel, **data},
    )

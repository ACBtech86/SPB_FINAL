"""Message form processing routes.

Replaces msgmenu.asp, ValidateMsg.asp, ProcessSPBForm.asp, MsgFormXml.asp.

Note: Form catalog operations use catalog_db (spb_messages.db).
      Message submission uses main db (spbsite.db).
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, get_catalog_db
from app.dependencies import get_current_user
from app.templates_config import templates
from spb_shared.models import User
from app.services.form_engine import get_message_types, load_form, validate_form
from app.services.xml_builder import build_spb_xml, submit_message

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/select", response_class=HTMLResponse)
async def message_selector(
    request: Request,
    catalog_db: AsyncSession = Depends(get_catalog_db),
    user: User = Depends(get_current_user),
):
    """Message type selector dropdown (replaces msgmenu.asp)."""
    msg_types = await get_message_types(catalog_db)
    return templates.TemplateResponse(
        "messages/selector.html",
        {"request": request, "user": user, "msg_types": msg_types},
    )


@router.get("/form/{msg_id}", response_class=HTMLResponse)
async def message_form(
    request: Request,
    msg_id: str,
    catalog_db: AsyncSession = Depends(get_catalog_db),
    user: User = Depends(get_current_user),
):
    """Render dynamic form for a specific message type."""
    form_def = await load_form(catalog_db, msg_id)
    if not form_def:
        return templates.TemplateResponse(
            "messages/selector.html",
            {"request": request, "user": user, "msg_types": [], "error": "Mensagem nao encontrada."},
        )
    return templates.TemplateResponse(
        "messages/form.html",
        {"request": request, "user": user, "form_def": form_def},
    )


@router.get("/combined", response_class=HTMLResponse)
async def message_combined(
    request: Request,
    catalog_db: AsyncSession = Depends(get_catalog_db),
    user: User = Depends(get_current_user),
):
    """Combined page with selector and form (replaces separate selector/form pages)."""
    msg_types = await get_message_types(catalog_db)
    return templates.TemplateResponse(
        "messages/combined.html",
        {"request": request, "user": user, "msg_types": msg_types},
    )


@router.get("/api/form/{msg_id}")
async def get_form_api(
    msg_id: str,
    catalog_db: AsyncSession = Depends(get_catalog_db),
    user: User = Depends(get_current_user),
):
    """API endpoint to get form definition as JSON."""
    form_def = await load_form(catalog_db, msg_id)
    if not form_def:
        return JSONResponse(
            status_code=404,
            content={"error": "Mensagem não encontrada"}
        )

    # Convert form_def to dict
    return JSONResponse(content={
        "msg_id": form_def.msg_id,
        "msg_descr": form_def.msg_descr,
        "fields": [
            {
                "cpotag": f.cpotag,
                "cponome": f.cponome,
                "cpoform": f.cpoform,
                "cpotam": f.cpotam,
                "cpoobrig": f.cpoobrig,
                "level": f.level,
                "is_group_start": f.is_group_start,
            }
            for f in form_def.fields
        ]
    })


@router.post("/submit", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    db: AsyncSession = Depends(get_db),
    catalog_db: AsyncSession = Depends(get_catalog_db),
    user: User = Depends(get_current_user),
):
    """Validate form and generate XML message."""
    form_data = dict(await request.form())
    msg_id = form_data.pop("formName", "")

    # Check if request wants JSON response (from combined page)
    accept_header = request.headers.get("accept", "")
    wants_json = "application/json" in accept_header or request.headers.get("x-requested-with") == "XMLHttpRequest"

    if not msg_id:
        if wants_json:
            return JSONResponse(content={"success": False, "errors": ["Tipo de mensagem não especificado"]})
        return RedirectResponse(url="/messages/select", status_code=303)

    # Load form definition for validation (from catalog db)
    form_def = await load_form(catalog_db, msg_id)
    if not form_def:
        if wants_json:
            return JSONResponse(content={"success": False, "errors": ["Mensagem não encontrada"]})
        return templates.TemplateResponse(
            "messages/form.html",
            {"request": request, "user": user, "form_def": None, "error": "Mensagem nao encontrada."},
        )

    # Validate
    validation = validate_form(form_def, form_data)
    if not validation.is_valid:
        if wants_json:
            return JSONResponse(content={"success": False, "errors": validation.errors})
        return templates.TemplateResponse(
            "messages/form.html",
            {"request": request, "user": user, "form_def": form_def, "errors": validation.errors, "form_data": form_data},
        )

    # Build XML and submit (to main db)
    try:
        xml_string, nu_ope, dest_table, queue_name = await build_spb_xml(catalog_db, msg_id, form_data)
        await submit_message(db, xml_string, msg_id, nu_ope, dest_table, queue_name)
    except ValueError as e:
        if wants_json:
            return JSONResponse(content={"success": False, "errors": [str(e)]})
        return templates.TemplateResponse(
            "messages/form.html",
            {"request": request, "user": user, "form_def": form_def, "errors": [str(e)], "form_data": form_data},
        )

    if wants_json:
        return JSONResponse(content={
            "success": True,
            "nu_ope": nu_ope,
            "dest_table": dest_table,
            "queue_name": queue_name,
        })

    return templates.TemplateResponse(
        "messages/form.html",
        {
            "request": request,
            "user": user,
            "form_def": form_def,
            "success": True,
            "nu_ope": nu_ope,
            "dest_table": dest_table,
            "queue_name": queue_name,
        },
    )

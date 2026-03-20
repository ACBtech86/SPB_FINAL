"""Message form processing routes.

Replaces msgmenu.asp, ValidateMsg.asp, ProcessSPBForm.asp, MsgFormXml.asp.
"""

from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user
from app.templates_config import templates
from spb_shared.models import User
from app.config import settings
from app.services.form_engine import get_message_types, load_form, validate_form
from app.services.xml_builder import build_spb_xml, submit_message
from app.services.query_messages import query_messages

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/select", response_class=HTMLResponse)
async def message_selector(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Message type selector dropdown (replaces msgmenu.asp)."""
    msg_types = await get_message_types(db, user)
    return templates.TemplateResponse(
        "messages/selector.html",
        {"request": request, "user": user, "msg_types": msg_types},
    )


@router.get("/form/{msg_id}", response_class=HTMLResponse)
async def message_form(
    request: Request,
    msg_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Render dynamic form for a specific message type."""
    form_def = await load_form(db, msg_id)
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
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Combined page with selector and form (replaces separate selector/form pages)."""
    msg_types = await get_message_types(db, user)
    return templates.TemplateResponse(
        "messages/combined.html",
        {"request": request, "user": user, "msg_types": msg_types, "settings": settings},
    )


@router.get("/api/form/{msg_id}")
async def get_form_api(
    msg_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """API endpoint to get form definition as JSON."""
    form_def = await load_form(db, msg_id)
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
                "cpotipo": f.cpotipo,
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

    # Load form definition for validation
    form_def = await load_form(db, msg_id)
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

    # Build XML and submit
    try:
        xml_string, nu_ope, dest_table, queue_name = await build_spb_xml(db, msg_id, form_data)
        await submit_message(db, xml_string, msg_id, nu_ope, dest_table, queue_name)
    except Exception as e:
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


@router.get("/query", response_class=HTMLResponse)
async def message_query(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    data_ini: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    hora_ini: Optional[str] = Query(None),
    hora_fim: Optional[str] = Query(None),
    grupo_msg: Optional[str] = Query(None),
    tipo_msg: Optional[str] = Query(None),
    situacao: Optional[str] = Query(None),
    mensagens: Optional[str] = Query("todas"),
    cpf_cnpj: Optional[str] = Query(None),
    nome_cliente: Optional[str] = Query(None),
    conta_creditada: Optional[str] = Query(None),
    conta_debitada: Optional[str] = Query(None),
    agencia_cred: Optional[str] = Query(None),
    agencia_deb: Optional[str] = Query(None),
    valor_ini: Optional[str] = Query(None),
    valor_fim: Optional[str] = Query(None),
    num_ctrl: Optional[str] = Query(None),
    if_contraparte: Optional[str] = Query(None),
    cod_leg: Optional[str] = Query(None),
    num_msg: Optional[str] = Query(None),
    ordenar: Optional[str] = Query("num_msg"),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=200),
):
    """Consultar Mensagens page (replaces consultarmsg)."""
    filters = {
        "data_ini": data_ini,
        "data_fim": data_fim,
        "hora_ini": hora_ini,
        "hora_fim": hora_fim,
        "grupo_msg": grupo_msg,
        "tipo_msg": tipo_msg,
        "situacao": situacao,
        "mensagens": mensagens or "todas",
        "cpf_cnpj": cpf_cnpj,
        "nome_cliente": nome_cliente,
        "conta_creditada": conta_creditada,
        "conta_debitada": conta_debitada,
        "agencia_cred": agencia_cred,
        "agencia_deb": agencia_deb,
        "valor_ini": valor_ini,
        "valor_fim": valor_fim,
        "num_ctrl": num_ctrl,
        "if_contraparte": if_contraparte,
        "cod_leg": cod_leg,
        "num_msg": num_msg,
        "ordenar": ordenar or "num_msg",
    }

    from datetime import date as _date
    today = _date.today().strftime("%d/%m/%Y")

    # System groups for dropdown
    sistemas = [
        "BMC", "CAM", "CCR", "CCS", "CIR", "CMP", "COR", "CQL", "CSD", "CTP",
        "DDA", "ECR", "GEN", "LDL", "LEI", "LFL", "LPI", "LTR", "PAG", "PTX",
        "RCO", "RDC", "SEL", "SLB", "SLC", "SME", "SML", "SRC", "STR", "TES",
    ]

    has_search = data_ini is not None
    result = await query_messages(db, filters, page, page_size) if has_search else None

    return templates.TemplateResponse(
        "messages/query.html",
        {
            "request": request,
            "user": user,
            "settings": settings,
            "filters": filters,
            "result": result,
            "page": page,
            "page_size": page_size,
            "today": today,
            "sistemas": sistemas,
        },
    )

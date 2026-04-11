"""XML message viewer routes.

Replaces ShwMsg.asp and ReportMsg.asp.
"""

import re
from datetime import datetime
from xml.etree import ElementTree as ET
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.templates_config import templates
from spb_shared.models import (
    User,
    SPBBacenToLocal,
    SPBSelicToLocal,
    SPBLocalToBacen,
    SPBLocalToSelic,
    SPBMensagem,
    SPBLogBacen,
    Fila,
)
from app.services.xml_utils import parse_xml, xml_to_tree

router = APIRouter(prefix="/viewer", tags=["viewer"])

ALLOWED_TABLES = {
    "spb_bacen_to_local",
    "spb_selic_to_local",
    "spb_local_to_bacen",
    "spb_local_to_selic",
    "fila",
}

TABLE_MODELS = {
    "spb_bacen_to_local": SPBBacenToLocal,
    "spb_selic_to_local": SPBSelicToLocal,
    "spb_local_to_bacen": SPBLocalToBacen,
    "spb_local_to_selic": SPBLocalToSelic,
    "fila": Fila,
}

# ISPB code -> friendly name
ISPB_NAMES = {
    "00038166": "Bacen",
    "36266751": "FINVEST",
    "00038121": "SELIC",
}

# Tag descriptions for the field table
TAG_DESCRIPTIONS = {
    "CodMsg": "Código Mensagem",
    "Id_Emissor": "ISPB Emissor",
    "Id_Destinatario": "ISPB Destinatário",
    "ISPBEmissor": "ISPB Emissor",
    "ISPBDestinatario": "ISPB Destinatário",
    "NUOp": "NU Operação",
    "NumCtrlIF": "Número Controle IF",
    "NumCtrlIFOrigem": "Núm. Controle IF Origem",
    "NumCtrlSTR": "Número Controle STR",
    "DtHrBC": "Data/Hora BC",
    "DtMovto": "Data Movimento",
    "VlrLanc": "Valor",
    "Valor": "Valor",
    "TipoLanc": "Tipo Lançamento",
    "CNPJ_CPFCredtd": "CPF/CNPJ Creditado",
    "NomCliCredtd": "Nome Cliente Creditado",
    "AgCredtd": "Agência Creditado",
    "CtCredtd": "Conta Creditado",
    "CNPJ_CPFDebtd": "CPF/CNPJ Debitado",
    "NomCliDebtd": "Nome Cliente Debitado",
    "AgDebtd": "Agência Debitado",
    "CtDebtd": "Conta Debitado",
    "CodSitRetReq": "Código Situação Retorno",
    "DescrSitRetReq": "Descrição Situação",
    "TipoId_Emissor": "Tipo Id Emissor",
    "TipoId_Destinatario": "Tipo Id Destinatário",
}

_NS_RE = re.compile(r"\{[^}]+\}")


def _strip_ns(tag: str) -> str:
    return _NS_RE.sub("", tag)


def _format_value(tag: str, value: str) -> str:
    """Return a human-friendly version of a raw XML value."""
    if not value:
        return ""

    # ISPB → name
    if tag in ("Id_Emissor", "Id_Destinatario", "ISPBEmissor", "ISPBDestinatario"):
        return ISPB_NAMES.get(value, value)

    # ISO datetime → dd/mm/yyyy HH:MM:SS
    if "T" in value and len(value) >= 19:
        try:
            dt = datetime.fromisoformat(value.split(".")[0].replace("Z", ""))
            return dt.strftime("%d/%m/%Y %H:%M:%S")
        except (ValueError, IndexError):
            pass

    # ISO date → dd/mm/yyyy
    if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        try:
            dt = datetime.strptime(value, "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            pass

    return value


def _extract_fields(xml_str: str) -> list[dict]:
    """Walk the XML and produce an ordered list of leaf field dicts.

    Each entry: {tag, descr, conteudo, formatado}
    """
    if not xml_str:
        return []

    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError:
        return []

    fields = []
    seen = set()
    for elem in root.iter():
        # Only leaf elements with text
        if list(elem):
            continue
        if elem.text is None or not elem.text.strip():
            continue
        tag = _strip_ns(elem.tag)
        if tag in seen:
            continue
        seen.add(tag)
        value = elem.text.strip()
        fields.append({
            "tag": tag,
            "descr": TAG_DESCRIPTIONS.get(tag, tag),
            "conteudo": value,
            "formatado": _format_value(tag, value),
        })
    return fields


def _direction_label(table: str, cod_msg: str) -> str:
    """Build the header tag like 'R - Recebido COD' or 'E - Enviado'."""
    if table.startswith("spb_local_"):
        return f"E - Enviado{(' ' + cod_msg) if cod_msg else ''}"
    return f"R - Recebido{(' ' + cod_msg) if cod_msg else ''}"


def _decode_situacao(flag_proc: str, status_msg: str) -> str:
    if flag_proc == "N" and status_msg == "N":
        return "Aguardando Piloto"
    if flag_proc == "E" and status_msg == "N":
        return "Enviada"
    if flag_proc == "E" and status_msg == "S":
        return "Mensagem Processada Corretamente"
    if flag_proc == "E" and status_msg == "R":
        return "Recebida"
    if flag_proc == "E" and status_msg == "E":
        return "Erro"
    if flag_proc == "C":
        return "Cancelada"
    return f"{flag_proc}/{status_msg}".strip("/")


async def _load_record(db: AsyncSession, table: str, record_id: str):
    """Load the record by composite key. Returns (record, xml_content) or (None, None)."""
    if table == "fila":
        seq = int(record_id)
        result = await db.execute(select(Fila).where(Fila.seq == seq))
        record = result.scalar_one_or_none()
        return record, (record.msg_xml if record else None)

    parts = record_id.split("_", 1)
    if len(parts) != 2:
        raise ValueError("Invalid composite key format")

    dt_str, msg_id_hex = parts
    db_datetime = datetime.fromisoformat(dt_str)
    mq_msg_id = bytes.fromhex(msg_id_hex)

    model = TABLE_MODELS[table]
    result = await db.execute(
        select(model).where(
            model.db_datetime == db_datetime,
            model.mq_msg_id == mq_msg_id,
        )
    )
    record = result.scalar_one_or_none()
    return record, (record.msg if record else None)


@router.get("/xml/{table}/{record_id:path}", response_class=HTMLResponse)
async def view_xml_raw(
    request: Request,
    table: str,
    record_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Pure XML viewer with collapsible tree, opened from the XML button."""
    if table not in ALLOWED_TABLES:
        return templates.TemplateResponse(
            "messages/viewer_xml.html",
            {"request": request, "user": user, "error": "Tabela não permitida."},
        )

    try:
        record, xml_content = await _load_record(db, table, record_id)
    except (ValueError, AttributeError) as e:
        return templates.TemplateResponse(
            "messages/viewer_xml.html",
            {"request": request, "user": user, "error": f"ID inválido: {e}"},
        )

    tree = None
    if xml_content:
        root = parse_xml(xml_content)
        if root is not None:
            tree = xml_to_tree(root)

    return templates.TemplateResponse(
        "messages/viewer_xml.html",
        {
            "request": request,
            "user": user,
            "xml_content": xml_content,
            "tree": tree,
            "cod_msg": getattr(record, "cod_msg", None) if record else None,
        },
    )


@router.get("/{table}/{record_id:path}", response_class=HTMLResponse)
async def view_xml(
    request: Request,
    table: str,
    record_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Show the formatted message viewer (legacy SPB layout)."""
    if table not in ALLOWED_TABLES:
        return templates.TemplateResponse(
            "messages/viewer.html",
            {"request": request, "user": user, "error": "Tabela não permitida."},
        )

    try:
        record, xml_content = await _load_record(db, table, record_id)
    except (ValueError, AttributeError) as e:
        return templates.TemplateResponse(
            "messages/viewer.html",
            {"request": request, "user": user, "error": f"ID inválido: {e}"},
        )

    if record is None:
        return templates.TemplateResponse(
            "messages/viewer.html",
            {"request": request, "user": user, "error": "Mensagem não encontrada."},
        )

    cod_msg = getattr(record, "cod_msg", "") or ""
    nu_ope = getattr(record, "nu_ope", "") or ""
    flag_proc = getattr(record, "flag_proc", "") or ""
    status_msg = getattr(record, "status_msg", "") or ""
    db_dt = getattr(record, "db_datetime", None)
    mq_dt = (
        getattr(record, "mq_datetime_put", None)
        or getattr(record, "mq_datetime", None)
    )

    # Description from catalog
    descr_result = await db.execute(
        select(SPBMensagem.msg_descr).where(SPBMensagem.msg_id == cod_msg)
    )
    msg_descr = descr_result.scalar_one_or_none() or ""

    # Extract fields, then add description column for CodMsg row
    fields = _extract_fields(xml_content or "")
    for f in fields:
        if f["tag"] == "CodMsg" and msg_descr:
            f["formatado"] = msg_descr

    # Related messages via mq_correl_id correlation. Two cases:
    #   (a) responses TO this message: opposite_table.mq_correl_id == this.mq_msg_id
    #   (b) the parent request this message responds to: any_table.mq_msg_id == this.mq_correl_id
    related = []
    opposite_map = {
        "spb_local_to_bacen": ("spb_bacen_to_local", SPBBacenToLocal),
        "spb_bacen_to_local": ("spb_local_to_bacen", SPBLocalToBacen),
        "spb_local_to_selic": ("spb_selic_to_local", SPBSelicToLocal),
        "spb_selic_to_local": ("spb_local_to_selic", SPBLocalToSelic),
    }
    opp_table, opp_model = opposite_map.get(table, (None, None))

    def _build_related_entry(rec, rec_table):
        rid = ""
        if rec.db_datetime and rec.mq_msg_id:
            rid = f"{rec.db_datetime.isoformat()}_{rec.mq_msg_id.hex()}"
        return {
            "hora": rec.db_datetime.strftime("%H:%M:%S") if rec.db_datetime else "",
            "data": rec.db_datetime.strftime("%d/%m/%Y") if rec.db_datetime else "",
            "cod_msg": rec.cod_msg or "",
            "situacao": _decode_situacao(
                getattr(rec, "flag_proc", "") or "",
                getattr(rec, "status_msg", "") or "",
            ),
            "viewer_url": f"/viewer/{rec_table}/{rid}" if rid else "",
        }

    # (a) Responses to this message
    if opp_model is not None and record.mq_msg_id:
        resp_result = await db.execute(
            select(opp_model)
            .where(opp_model.mq_correl_id == record.mq_msg_id)
            .order_by(opp_model.db_datetime.asc())
        )
        for resp in resp_result.scalars().all():
            related.append(_build_related_entry(resp, opp_table))

    # (b) Parent request this message answers
    parent_correl = getattr(record, "mq_correl_id", None)
    if parent_correl and opp_model is not None:
        # Skip empty/null-byte correlation IDs
        if any(b for b in parent_correl):
            par_result = await db.execute(
                select(opp_model)
                .where(opp_model.mq_msg_id == parent_correl)
                .order_by(opp_model.db_datetime.asc())
            )
            for par in par_result.scalars().all():
                related.append(_build_related_entry(par, opp_table))

    # Audit entries from spb_log_bacen by nu_ope
    autorizacoes = []
    if nu_ope:
        log_result = await db.execute(
            select(SPBLogBacen)
            .where(SPBLogBacen.nu_ope == nu_ope)
            .order_by(SPBLogBacen.db_datetime.asc())
            .limit(20)
        )
        for log in log_result.scalars().all():
            autorizacoes.append({
                "cod_usuario": "BCSrvSqlMq",
                "tipo": "Sistema",
                "nome": "BCSrvSqlMq",
                "situacao": _decode_situacao(
                    getattr(log, "flag_proc", "") or "",
                    getattr(log, "status_msg", "") or "",
                ),
                "data": log.db_datetime.strftime("%d/%m/%Y") if log.db_datetime else "",
                "hora": log.db_datetime.strftime("%H:%M:%S") if log.db_datetime else "",
                "area": log.cod_msg or "",
            })

    # Header info
    msg_num = db_dt.strftime("%y%m%d%H%M%S") if db_dt else record_id[:14]
    direction_label = _direction_label(table, cod_msg)
    hora_prevista = mq_dt.strftime("%H:%M:%S") if mq_dt else ""
    hora_limite = db_dt.strftime("%H:%M:%S") if db_dt else ""

    return templates.TemplateResponse(
        "messages/viewer.html",
        {
            "request": request,
            "user": user,
            "table": table,
            "record_id": record_id,
            "msg_num": msg_num,
            "direction_label": direction_label,
            "hora_prevista": hora_prevista,
            "hora_limite": hora_limite,
            "cod_msg": cod_msg,
            "msg_descr": msg_descr,
            "fields": fields,
            "related": related,
            "autorizacoes": autorizacoes,
            "xml_url": f"/viewer/xml/{table}/{record_id}",
            "xml_content": xml_content,
        },
    )


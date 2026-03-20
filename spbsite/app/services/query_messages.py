"""Service for querying/filtering SPB messages (Consultar Mensagens).

Queries spb_local_to_bacen (sent) and spb_bacen_to_local (received),
parses XML to extract display fields, and applies filters.
"""

import re
import math
from datetime import datetime, date
from typing import Any, Optional
from xml.etree import ElementTree as ET

from sqlalchemy import select, and_, or_, func, cast, String, text
from sqlalchemy.ext.asyncio import AsyncSession

from spb_shared.models import SPBLocalToBacen, SPBBacenToLocal, SPBMensagem


# XML tag extraction - strips namespace prefix
_NS_RE = re.compile(r'\{[^}]+\}')


def _strip_ns(tag: str) -> str:
    return _NS_RE.sub('', tag)


def _xml_extract(xml_str: Optional[str]) -> dict[str, str]:
    """Extract key fields from SPB message XML for display."""
    result = {
        'ispb_emissor': '', 'ispb_destinatario': '',
        'valor': '', 'dc': '',
        'cpf_cnpj_cred': '', 'nome_cli_cred': '', 'conta_cred': '', 'ag_cred': '',
        'cpf_cnpj_deb': '', 'nome_cli_deb': '', 'conta_deb': '', 'ag_deb': '',
        'num_ctrl_if': '',
    }
    if not xml_str:
        return result

    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError:
        return result

    # Build flat dict of all leaf elements (strip namespaces)
    flat = {}
    for elem in root.iter():
        tag = _strip_ns(elem.tag)
        if elem.text and elem.text.strip():
            flat[tag] = elem.text.strip()

    # Map XML tags to display fields
    result['ispb_emissor'] = flat.get('ISPBEmissor', flat.get('Id_Emissor', ''))
    result['ispb_destinatario'] = flat.get('ISPBDestinatario', flat.get('Id_Destinatario', ''))

    # Value fields (STR/PAG messages)
    result['valor'] = flat.get('VlrLanc', flat.get('Valor', ''))

    # Debit side
    result['cpf_cnpj_deb'] = flat.get('CNPJ_CPFDebtd', flat.get('CNPJCPFDebtd', ''))
    result['nome_cli_deb'] = flat.get('NomCliDebtd', flat.get('NomeCliDebtd', ''))
    result['conta_deb'] = flat.get('CtDebtd', '')
    result['ag_deb'] = flat.get('AgDebtd', '')

    # Credit side
    result['cpf_cnpj_cred'] = flat.get('CNPJ_CPFCredtd', flat.get('CNPJCPFCredtd', ''))
    result['nome_cli_cred'] = flat.get('NomCliCredtd', flat.get('NomeCliCredtd', ''))
    result['conta_cred'] = flat.get('CtCredtd', '')
    result['ag_cred'] = flat.get('AgCredtd', '')

    # Control
    result['num_ctrl_if'] = flat.get('NumCtrlIF', flat.get('NumCtrlIFOrigem', ''))

    return result


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


async def _get_msg_descriptions(db: AsyncSession) -> dict[str, str]:
    """Load MSG_ID -> MSG_DESCR mapping."""
    result = await db.execute(select(SPBMensagem.msg_id, SPBMensagem.msg_descr))
    return {row[0]: row[1] for row in result.all()}


async def query_messages(
    db: AsyncSession,
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 30,
) -> dict[str, Any]:
    """Query messages with filters, parse XML, return paginated results."""

    msg_descr_map = await _get_msg_descriptions(db)

    # Determine which tables to query
    msg_filter = filters.get('mensagens', 'todas')

    rows = []

    # Query sent messages
    if msg_filter in ('todas', 'enviadas', 'todas_r1'):
        sent = await _query_sent(db, filters)
        for row in sent:
            xml_data = _xml_extract(row.msg)
            rows.append(_build_row(row, 'E', msg_descr_map, xml_data))

    # Query received messages
    if msg_filter in ('todas', 'recebidas', 'todas_r1'):
        received = await _query_received(db, filters)
        for row in received:
            xml_data = _xml_extract(row.msg)
            rows.append(_build_row(row, 'R', msg_descr_map, xml_data))

    # Apply post-query XML-based filters
    rows = _apply_xml_filters(rows, filters)

    # Sort
    ordenar = filters.get('ordenar', 'num_msg')
    reverse = True
    if ordenar == 'num_msg':
        rows.sort(key=lambda r: r['db_datetime'], reverse=True)
    elif ordenar == 'valor':
        rows.sort(key=lambda r: r.get('valor_num', 0), reverse=True)
    elif ordenar == 'if_contraparte':
        rows.sort(key=lambda r: r.get('if_contraparte', ''))
        reverse = False
    elif ordenar == 'hora':
        rows.sort(key=lambda r: r['db_datetime'])
    elif ordenar == 'hora_desc':
        rows.sort(key=lambda r: r['db_datetime'], reverse=True)
    elif ordenar == 'hora_retorno':
        rows.sort(key=lambda r: r.get('hora_retorno') or datetime.min)
    elif ordenar == 'hora_retorno_desc':
        rows.sort(key=lambda r: r.get('hora_retorno') or datetime.min, reverse=True)

    # Assign sequential num_msg
    total = len(rows)
    for i, row in enumerate(rows):
        row['num_msg_seq'] = total - i

    # Paginate
    total_pages = max(1, math.ceil(total / page_size))
    page = min(page, total_pages)
    start = (page - 1) * page_size
    page_rows = rows[start:start + page_size]

    return {
        'rows': page_rows,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
    }


def _build_row(
    db_row, direction: str, msg_descr_map: dict, xml_data: dict
) -> dict[str, Any]:
    """Build display row dict from DB row + XML data."""
    cod_msg = getattr(db_row, 'cod_msg', '') or ''
    nu_ope = getattr(db_row, 'nu_ope', '') or ''
    db_dt = db_row.db_datetime

    # Determine D/C from message type
    dc = ''
    if cod_msg.startswith('STR') or cod_msg.startswith('PAG'):
        dc = 'D' if direction == 'E' else 'C'

    # IF Contraparte = the other ISPB
    if direction == 'E':
        if_contraparte = xml_data.get('ispb_destinatario', '')
    else:
        if_contraparte = xml_data.get('ispb_emissor', '')

    # Determine situation from flag_proc/status_msg
    flag_proc = getattr(db_row, 'flag_proc', '') or ''
    status_msg = getattr(db_row, 'status_msg', '') or ''
    situacao = _decode_situacao(flag_proc, status_msg)

    # Hora retorno (response timestamp)
    hora_retorno = getattr(db_row, 'mq_datetime_coa', None) or getattr(db_row, 'mq_datetime', None)

    # Parse valor to float for sorting
    valor_str = xml_data.get('valor', '')
    try:
        valor_num = float(valor_str.replace(',', '.')) if valor_str else 0
    except (ValueError, AttributeError):
        valor_num = 0

    return {
        'db_datetime': db_dt,
        'data_mov': db_dt.strftime('%d/%m/%Y') if db_dt else '',
        'data_reg': db_dt.strftime('%d/%m/%Y') if db_dt else '',
        'hora_reg': db_dt.strftime('%H:%M:%S') if db_dt else '',
        'hora_retorno': hora_retorno,
        'hora_retorno_str': hora_retorno.strftime('%H:%M:%S') if hora_retorno else '',
        'cod_msg': cod_msg,
        'descricao': msg_descr_map.get(cod_msg, ''),
        'if_contraparte': if_contraparte,
        'valor': valor_str,
        'valor_num': valor_num,
        'dc': dc,
        'situacao': situacao,
        'status': status_msg,
        'num_ctrl_if': xml_data.get('num_ctrl_if', ''),
        'nu_ope': nu_ope,
        'cpf_cnpj_cred': xml_data.get('cpf_cnpj_cred', ''),
        'nome_cli_cred': xml_data.get('nome_cli_cred', ''),
        'conta_cred': xml_data.get('conta_cred', ''),
        'ag_cred': xml_data.get('ag_cred', ''),
        'cpf_cnpj_deb': xml_data.get('cpf_cnpj_deb', ''),
        'nome_cli_deb': xml_data.get('nome_cli_deb', ''),
        'conta_deb': xml_data.get('conta_deb', ''),
        'ag_deb': xml_data.get('ag_deb', ''),
        'direction': direction,
    }


def _decode_situacao(flag_proc: str, status_msg: str) -> str:
    """Decode flag_proc + status_msg into human-readable situation."""
    if flag_proc == 'N' and status_msg == 'N':
        return 'Aguardando Piloto'
    elif flag_proc == 'E' and status_msg == 'N':
        return 'Enviada'
    elif flag_proc == 'E' and status_msg == 'S':
        return 'Confirmada'
    elif flag_proc == 'E' and status_msg == 'E':
        return 'Erro'
    elif flag_proc == 'N' and status_msg == 'S':
        return 'Processada'
    elif flag_proc == 'C':
        return 'Cancelada'
    return f'{flag_proc}/{status_msg}'


async def _query_sent(db: AsyncSession, filters: dict) -> list:
    """Query spb_local_to_bacen with DB-level filters."""
    model = SPBLocalToBacen
    conditions = []

    d_ini = _parse_date(filters.get('data_ini'))
    d_fim = _parse_date(filters.get('data_fim'))
    if d_ini:
        conditions.append(model.db_datetime >= datetime.combine(d_ini, datetime.min.time()))
    if d_fim:
        conditions.append(model.db_datetime <= datetime.combine(d_fim, datetime.max.time()))

    tipo_msg = filters.get('tipo_msg')
    if tipo_msg:
        conditions.append(model.cod_msg == tipo_msg)

    grupo_msg = filters.get('grupo_msg')
    if grupo_msg and grupo_msg != 'Todos':
        conditions.append(model.cod_msg.like(f'{grupo_msg}%'))

    num_msg_filter = filters.get('num_msg')
    if num_msg_filter:
        conditions.append(cast(model.db_datetime, String).like(f'%{num_msg_filter}%'))

    # R1 filter: exclude R1/R2 messages unless explicitly requested
    msg_filter = filters.get('mensagens', 'todas')
    if msg_filter == 'enviadas':
        conditions.append(~model.cod_msg.like('%R1'))
        conditions.append(~model.cod_msg.like('%R2'))

    stmt = select(model)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(model.db_datetime.desc()).limit(500)

    result = await db.execute(stmt)
    return result.scalars().all()


async def _query_received(db: AsyncSession, filters: dict) -> list:
    """Query spb_bacen_to_local with DB-level filters."""
    model = SPBBacenToLocal
    conditions = []

    d_ini = _parse_date(filters.get('data_ini'))
    d_fim = _parse_date(filters.get('data_fim'))
    if d_ini:
        conditions.append(model.db_datetime >= datetime.combine(d_ini, datetime.min.time()))
    if d_fim:
        conditions.append(model.db_datetime <= datetime.combine(d_fim, datetime.max.time()))

    tipo_msg = filters.get('tipo_msg')
    if tipo_msg:
        conditions.append(model.cod_msg == tipo_msg)

    grupo_msg = filters.get('grupo_msg')
    if grupo_msg and grupo_msg != 'Todos':
        conditions.append(model.cod_msg.like(f'{grupo_msg}%'))

    msg_filter = filters.get('mensagens', 'todas')
    if msg_filter == 'recebidas':
        pass  # No extra filter
    elif msg_filter == 'enviadas':
        return []  # Don't query received table for "enviadas" filter

    stmt = select(model)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(model.db_datetime.desc()).limit(500)

    result = await db.execute(stmt)
    return result.scalars().all()


def _apply_xml_filters(rows: list[dict], filters: dict) -> list[dict]:
    """Apply filters that depend on parsed XML data."""
    result = rows

    cpf_cnpj = filters.get('cpf_cnpj')
    if cpf_cnpj:
        result = [r for r in result if cpf_cnpj in r.get('cpf_cnpj_cred', '') or cpf_cnpj in r.get('cpf_cnpj_deb', '')]

    nome_cliente = filters.get('nome_cliente')
    if nome_cliente:
        nome_upper = nome_cliente.upper()
        result = [r for r in result if nome_upper in r.get('nome_cli_cred', '').upper() or nome_upper in r.get('nome_cli_deb', '').upper()]

    conta_cred = filters.get('conta_creditada')
    if conta_cred:
        result = [r for r in result if conta_cred in r.get('conta_cred', '')]

    conta_deb = filters.get('conta_debitada')
    if conta_deb:
        result = [r for r in result if conta_deb in r.get('conta_deb', '')]

    ag_cred = filters.get('agencia_cred')
    if ag_cred:
        result = [r for r in result if ag_cred in r.get('ag_cred', '')]

    ag_deb = filters.get('agencia_deb')
    if ag_deb:
        result = [r for r in result if ag_deb in r.get('ag_deb', '')]

    if_contraparte = filters.get('if_contraparte')
    if if_contraparte and if_contraparte != 'Todos':
        result = [r for r in result if if_contraparte in r.get('if_contraparte', '')]

    num_ctrl = filters.get('num_ctrl')
    if num_ctrl:
        result = [r for r in result if num_ctrl in r.get('num_ctrl_if', '')]

    valor_ini = filters.get('valor_ini')
    valor_fim = filters.get('valor_fim')
    if valor_ini:
        try:
            v_ini = float(valor_ini.replace(',', '.'))
            result = [r for r in result if r.get('valor_num', 0) >= v_ini]
        except ValueError:
            pass
    if valor_fim:
        try:
            v_fim = float(valor_fim.replace(',', '.'))
            result = [r for r in result if r.get('valor_num', 0) <= v_fim]
        except ValueError:
            pass

    return result

"""Service layer for monitoring dashboard queries.

Replaces the RecordsetToXMLDoc pattern from inc/xmlutilbc.asp.
Instead of converting recordsets to XML then XSL-transforming to HTML,
we query directly with SQLAlchemy and pass results to Jinja2 templates.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import func, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from spb_shared.models import BacenControle, SPBControle
from spb_shared.models import SPBLogBacen, SPBLogSelic
from spb_shared.models import (
    SPBBacenToLocal,
    SPBLocalToBacen,
    SPBLocalToSelic,
    SPBSelicToLocal,
)

# Maps channel names to model classes
CONTROL_MODELS = {
    "local": SPBControle,
    "bacen": BacenControle,
}

INBOUND_MODELS = {
    "bacen": [SPBBacenToLocal],
    "selic": [SPBSelicToLocal],
    "all": [SPBBacenToLocal, SPBSelicToLocal],
}

OUTBOUND_MODELS = {
    "bacen": [SPBLocalToBacen],
    "selic": [SPBLocalToSelic],
    "all": [SPBLocalToBacen, SPBLocalToSelic],
}

LOG_MODELS = {
    "bacen": [SPBLogBacen],
    "selic": [SPBLogSelic],
    "all": [SPBLogBacen, SPBLogSelic],
}

# Page titles (Portuguese, matching originals)
CONTROL_TITLES = {
    "local": "Controle do STR Local",
    "bacen": "Controle do STR BACEN",
}

INBOUND_TITLES = {
    "all": "Mensagens Recebidas do SPB",
    "bacen": "Mensagens Recebidas do BACEN",
    "selic": "Mensagens Recebidas do SELIC",
}

OUTBOUND_TITLES = {
    "all": "Mensagens Enviadas para o SPB",
    "bacen": "Mensagens Enviadas para o BACEN",
    "selic": "Mensagens Enviadas para o SELIC",
}

LOG_TITLES = {
    "all": "Log do Sistema SPB",
    "bacen": "Log do Sistema BACEN",
    "selic": "Log do Sistema SELIC",
}


async def get_control_data(db: AsyncSession, channel: str) -> dict[str, Any]:
    """Query control/status table for the given channel."""
    model = CONTROL_MODELS[channel]
    result = await db.execute(select(model).order_by(model.nome_ispb))
    rows = result.scalars().all()

    # Compute statistics
    total = len(rows)
    status_n = sum(1 for r in rows if r.status_geral == "N")
    status_s = sum(1 for r in rows if r.status_geral == "S")

    return {
        "title": CONTROL_TITLES[channel],
        "rows": rows,
        "stats": {"total": total, "status_n": status_n, "status_s": status_s},
        "current_date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }


async def get_messages(
    db: AsyncSession, direction: str, channel: str, limit: int = 500, offset: int = 0
) -> dict[str, Any]:
    """Query inbound or outbound message tables."""
    models_map = INBOUND_MODELS if direction == "inbound" else OUTBOUND_MODELS
    titles_map = INBOUND_TITLES if direction == "inbound" else OUTBOUND_TITLES
    model_list = models_map[channel]

    all_rows = []
    for model in model_list:
        result = await db.execute(
            select(model).order_by(model.db_datetime.desc()).limit(limit).offset(offset)
        )
        all_rows.extend(result.scalars().all())

    # Sort combined results by db_datetime descending
    all_rows.sort(key=lambda r: r.db_datetime or datetime.min, reverse=True)

    # Compute statistics
    total = len(all_rows)
    total_req = 0
    total_rsp = 0
    queue_field = "mq_qn_origem" if direction == "inbound" else "mq_qn_destino"
    for row in all_rows:
        qn = getattr(row, queue_field, "") or ""
        if len(qn) >= 6:
            tipo = qn[3:6]
            if tipo == "REQ":
                total_req += 1
            elif tipo == "RSP":
                total_rsp += 1

    return {
        "title": titles_map[channel],
        "rows": all_rows[:limit],
        "direction": direction,
        "channel": channel,
        "stats": {"total": total, "total_req": total_req, "total_rsp": total_rsp},
        "current_date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }


async def get_logs(
    db: AsyncSession, channel: str, limit: int = 500, offset: int = 0
) -> dict[str, Any]:
    """Query system log tables."""
    model_list = LOG_MODELS[channel]

    all_rows = []
    for model in model_list:
        result = await db.execute(
            select(model).order_by(model.db_datetime.desc()).limit(limit).offset(offset)
        )
        all_rows.extend(result.scalars().all())

    all_rows.sort(key=lambda r: r.db_datetime or datetime.min, reverse=True)

    total = len(all_rows)
    total_n = sum(1 for r in all_rows if r.status_msg == "N")
    total_s = sum(1 for r in all_rows if r.status_msg == "S")

    return {
        "title": LOG_TITLES[channel],
        "rows": all_rows[:limit],
        "stats": {
            "total": total,
            "total_req": sum(1 for r in all_rows if (getattr(r, "mq_qn_origem", "") or "")[3:6] == "REQ"),
            "total_rep": sum(1 for r in all_rows if (getattr(r, "mq_qn_origem", "") or "")[3:6] == "REP"),
            "total_n": total_n,
            "total_s": total_s,
        },
        "current_date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }

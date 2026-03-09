"""Payment queue management service.

Replaces SPB/pr_calc3.asp and SPB/Atualiza.asp business logic.
"""

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from spb_shared.models import SPBMensagem
from spb_shared.models import Camaras, Fila


async def get_pending_messages(
    db: AsyncSession, catalog_db: AsyncSession
) -> list[dict[str, Any]]:
    """Get pending messages from the queue with descriptions.

    Replaces the JOIN query from pr_calc3.asp:
    SELECT Fila.*, SPB_MENSAGEM.MSG_DESCR FROM Fila
    INNER JOIN SPB_MENSAGEM ON Fila.Mensagem = SPB_MENSAGEM.MSG_ID
    ORDER BY Fila.Data

    Uses two sessions because Fila is in BCSPB and SPBMensagem is in spb_catalog.
    """
    # 1) Query Fila from the operational database (BCSPB)
    fila_query = select(Fila).order_by(Fila.data)
    fila_result = await db.execute(fila_query)
    fila_rows = fila_result.scalars().all()

    if not fila_rows:
        return []

    # 2) Collect unique message codes and fetch descriptions from catalog (spb_catalog)
    msg_codes = {row.mensagem for row in fila_rows if row.mensagem}
    descr_map: dict[str, str] = {}
    if msg_codes:
        cat_query = select(SPBMensagem.msg_id, SPBMensagem.msg_descr).where(
            SPBMensagem.msg_id.in_(msg_codes)
        )
        cat_result = await catalog_db.execute(cat_query)
        for row in cat_result.all():
            descr_map[row.msg_id] = row.msg_descr or ""

    # 3) Merge results
    messages = []
    for row in fila_rows:
        messages.append({
            "seq": row.seq,
            "valor": row.valor or Decimal("0"),
            "mensagem": row.mensagem,
            "descr": descr_map.get(row.mensagem, ""),
            "status": row.status,
            "tipo": row.tipo,
            "contraparte": row.contraparte,
            "data": row.data,
            "prdade": row.prdade,
            "msg_xml": row.msg_xml,
        })

    return messages


async def get_balance_summary(db: AsyncSession) -> dict[str, Any]:
    """Get clearinghouse balance summary from Camaras table."""
    result = await db.execute(select(Camaras).limit(1))
    camaras = result.scalar_one_or_none()

    if camaras:
        tot_str = camaras.tot_str or Decimal("0")
        tot_compe = camaras.tot_compe or Decimal("0")
        tot_cip = camaras.tot_cip or Decimal("0")
    else:
        tot_str = tot_compe = tot_cip = Decimal("0")

    return {
        "tot_str": tot_str,
        "tot_compe": tot_compe,
        "tot_cip": tot_cip,
        "total": tot_str + tot_compe + tot_cip,
    }


async def get_message_xml(db: AsyncSession, seq: int) -> str | None:
    """Get XML content for a specific message by sequence number."""
    result = await db.execute(select(Fila).where(Fila.seq == seq))
    fila = result.scalar_one_or_none()
    return fila.msg_xml if fila else None


async def process_selected(db: AsyncSession, seq_ids: list[int]) -> int:
    """Process selected messages from the queue.

    Updates the status of selected messages.
    Returns number of processed messages.
    """
    if not seq_ids:
        return 0

    count = 0
    for seq_id in seq_ids:
        result = await db.execute(select(Fila).where(Fila.seq == seq_id))
        fila = result.scalar_one_or_none()
        if fila:
            fila.status = "E"  # Enviado (sent)
            count += 1

    await db.commit()
    return count

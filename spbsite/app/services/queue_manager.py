"""Payment queue management service.

Replaces SPB/pr_calc3.asp and SPB/Atualiza.asp business logic.
"""

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from spb_shared.models import SPBMensagem
from spb_shared.models import Camaras, Fila


async def get_pending_messages(db: AsyncSession) -> list[dict[str, Any]]:
    """Get pending messages from the queue with descriptions.

    Replaces the JOIN query from pr_calc3.asp:
    SELECT Fila.*, SPB_MENSAGEM.MSG_DESCR FROM Fila
    INNER JOIN SPB_MENSAGEM ON Fila.Mensagem = SPB_MENSAGEM.MSG_ID
    ORDER BY Fila.Data
    """
    query = (
        select(
            Fila.seq,
            Fila.valor,
            Fila.mensagem,
            SPBMensagem.msg_descr,
            Fila.status,
            Fila.tipo,
            Fila.contraparte,
            Fila.data,
            Fila.prdade,
            Fila.msg_xml,
        )
        .join(SPBMensagem, Fila.mensagem == SPBMensagem.msg_id)
        .order_by(Fila.data)
    )

    result = await db.execute(query)
    rows = result.all()

    messages = []
    for row in rows:
        messages.append({
            "seq": row.seq,
            "valor": row.valor or Decimal("0"),
            "mensagem": row.mensagem,
            "descr": row.msg_descr or "",
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

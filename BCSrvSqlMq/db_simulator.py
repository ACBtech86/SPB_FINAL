#!/usr/bin/env python
"""
Database-only SPB Message Simulator
Simulates BCSrvSqlMq + BACEN without requiring IBM MQ or pymqi.

Monitors spb_local_to_bacen and generates responses in spb_bacen_to_local.
"""
import asyncio
import sys
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://postgres:Rama1248@localhost:5432/BanuxSPB"

# ISPB codes
ISPB_LOCAL = "36266751"
ISPB_BACEN = "00038166"

async def generate_bacen_response(msg_id: str, nu_ope: str, original_msg: str) -> str:
    """Generate a simulated BACEN response based on message type."""

    # Simple response template
    response_template = f"""<?xml version="1.0" encoding="UTF-8"?>
<DOC xmlns="http://www.bcb.gov.br/SPB/gen/{msg_id.lower()}">
    <BCMSG>
        <IdentdPartDestMSG>BACEN</IdentdPartDestMSG>
        <IdentdPartMSG>{ISPB_LOCAL}</IdentdPartMSG>
        <NumCtrlMSG>{nu_ope}</NumCtrlMSG>
        <TpAmb>P</TpAmb>
    </BCMSG>
    <SISARQ>
        <RspGer>
            <IndrResp>A</IndrResp>
            <DescResp>Mensagem aceita com sucesso</DescResp>
        </RspGer>
    </SISARQ>
</DOC>"""

    return response_template


async def process_outbound_messages(db: AsyncSession):
    """Process pending outbound messages and generate responses."""

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking for pending messages...")

    # Find messages waiting to be processed
    result = await db.execute(text("""
        SELECT db_datetime, cod_msg, nu_ope, msg, mq_qn_destino
        FROM spb_local_to_bacen
        WHERE flag_proc = 'P' AND status_msg = 'P'
        ORDER BY db_datetime
        LIMIT 10
    """))

    messages = result.fetchall()

    if not messages:
        return 0

    print(f"\n{'='*80}")
    print(f"Found {len(messages)} pending message(s)")
    print(f"{'='*80}\n")

    processed = 0

    for msg_row in messages:
        db_datetime, cod_msg, nu_ope, msg_content, mq_qn_destino = msg_row

        print(f"Processing message:")
        print(f"  Time: {db_datetime}")
        print(f"  Type: {cod_msg}")
        print(f"  Nu_Ope: {nu_ope}")
        print(f"  Queue: {mq_qn_destino}")

        try:
            # Simulate "sending to MQ" - update timestamp
            await db.execute(text("""
                UPDATE spb_local_to_bacen
                SET mq_datetime_put = NOW()
                WHERE db_datetime = :db_datetime AND cod_msg = :cod_msg
            """), {"db_datetime": db_datetime, "cod_msg": cod_msg})

            print(f"  [OK] Simulated MQ PUT")

            # Generate BACEN response
            response_msg = await generate_bacen_response(cod_msg, nu_ope, msg_content)

            # Insert response into inbound table
            response_queue = f"QL.RSP.{ISPB_BACEN}.{ISPB_LOCAL}.01"

            await db.execute(text("""
                INSERT INTO spb_bacen_to_local (
                    mq_msg_id, mq_correl_id, db_datetime, status_msg, flag_proc,
                    mq_qn_origem, mq_datetime, mq_header, security_header,
                    nu_ope, cod_msg, msg
                ) VALUES (
                    :mq_msg_id, :mq_correl_id, NOW(), 'P', 'P',
                    :mq_qn_origem, NOW(), :mq_header, :security_header,
                    :nu_ope, :cod_msg, :msg
                )
            """), {
                "mq_msg_id": b'\x00' * 24,  # Dummy message ID
                "mq_correl_id": b'\x00' * 24,  # Dummy correlation ID
                "mq_qn_origem": response_queue,
                "mq_header": b'',
                "security_header": b'',
                "nu_ope": nu_ope,
                "cod_msg": f"{cod_msg}R1",  # Response type
                "msg": response_msg
            })

            print(f"  [OK] Generated response: {cod_msg}R1")
            print(f"  [OK] Inserted into spb_bacen_to_local")

            # Mark original message as processed
            await db.execute(text("""
                UPDATE spb_local_to_bacen
                SET status_msg = 'S', flag_proc = 'S', mq_datetime_rep = NOW()
                WHERE db_datetime = :db_datetime AND cod_msg = :cod_msg
            """), {"db_datetime": db_datetime, "cod_msg": cod_msg})

            print(f"  [OK] Marked original as processed")

            await db.commit()
            processed += 1

            print(f"\n  SUCCESS! Message flow complete.\n")

        except Exception as e:
            print(f"  ERROR: {e}")
            await db.rollback()
            raise

    return processed


async def monitor_loop():
    """Main monitoring loop."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("="*80)
    print("SPB DATABASE SIMULATOR")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: BanuxSPB")
    print(f"Mode: Simulation (no real MQ)")
    print("="*80)
    print("\nMonitoring for outbound messages...")
    print("Press Ctrl+C to stop\n")

    try:
        cycle = 0
        while True:
            cycle += 1

            async with async_session() as db:
                try:
                    processed = await process_outbound_messages(db)
                    if processed > 0:
                        print(f"\nCycle {cycle}: Processed {processed} message(s)")
                except Exception as e:
                    print(f"ERROR in cycle {cycle}: {e}")
                    import traceback
                    traceback.print_exc()

            # Check every 3 seconds
            await asyncio.sleep(3)

    except KeyboardInterrupt:
        print("\n\nSimulator stopped by user.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("\nStarting Database Simulator...\n")
    asyncio.run(monitor_loop())

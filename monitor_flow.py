#!/usr/bin/env python
"""Monitor message flow through SPB system."""
import asyncio
import sys
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://postgres:Rama1248@localhost:5432/BanuxSPB"

async def monitor():
    """Monitor message tables for new entries."""
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("=" * 80)
    print("SPB MESSAGE FLOW MONITOR")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nWatching for new messages...")
    print("-" * 80)

    # Get initial counts
    async with async_session() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM spb_local_to_bacen"))
        initial_outbound = result.scalar()

        result = await session.execute(text("SELECT COUNT(*) FROM spb_bacen_to_local"))
        initial_inbound = result.scalar()

    print(f"Initial state:")
    print(f"  Outbound (spb_local_to_bacen): {initial_outbound}")
    print(f"  Inbound (spb_bacen_to_local): {initial_inbound}")
    print("\nMonitoring for changes (Ctrl+C to stop)...\n")

    last_outbound = initial_outbound
    last_inbound = initial_inbound

    try:
        while True:
            await asyncio.sleep(2)  # Check every 2 seconds

            async with async_session() as session:
                # Check outbound messages
                result = await session.execute(text("""
                    SELECT db_datetime, status_msg, flag_proc, mq_qn_destino,
                           cod_msg, nu_ope, LEFT(msg, 100) as msg_preview
                    FROM spb_local_to_bacen
                    ORDER BY db_datetime DESC
                    LIMIT 3
                """))
                outbound_rows = result.fetchall()
                current_outbound = len(outbound_rows) if outbound_rows else 0

                result = await session.execute(text("SELECT COUNT(*) FROM spb_local_to_bacen"))
                total_outbound = result.scalar()

                # Check inbound messages
                result = await session.execute(text("""
                    SELECT db_datetime, status_msg, flag_proc, mq_qn_origem,
                           cod_msg, nu_ope, LEFT(msg, 100) as msg_preview
                    FROM spb_bacen_to_local
                    ORDER BY db_datetime DESC
                    LIMIT 3
                """))
                inbound_rows = result.fetchall()

                result = await session.execute(text("SELECT COUNT(*) FROM spb_bacen_to_local"))
                total_inbound = result.scalar()

                # Report changes
                if total_outbound != last_outbound:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] NEW OUTBOUND MESSAGE!")
                    print(f"  Total outbound: {last_outbound} -> {total_outbound} (+{total_outbound - last_outbound})")
                    if outbound_rows:
                        for row in outbound_rows[:1]:  # Show latest
                            print(f"  Time: {row[0]}")
                            print(f"  Status: {row[1]}, Flag: {row[2]}")
                            print(f"  Queue: {row[3]}")
                            print(f"  Message: {row[4]} (Nu_Ope: {row[5]})")
                            if row[6]:
                                print(f"  Preview: {row[6][:80]}...")
                    last_outbound = total_outbound

                if total_inbound != last_inbound:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] NEW INBOUND MESSAGE!")
                    print(f"  Total inbound: {last_inbound} -> {total_inbound} (+{total_inbound - last_inbound})")
                    if inbound_rows:
                        for row in inbound_rows[:1]:  # Show latest
                            print(f"  Time: {row[0]}")
                            print(f"  Status: {row[1]}, Flag: {row[2]}")
                            print(f"  Queue: {row[3]}")
                            print(f"  Message: {row[4]} (Nu_Ope: {row[5]})")
                            if row[6]:
                                print(f"  Preview: {row[6][:80]}...")
                    last_inbound = total_inbound

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(monitor())

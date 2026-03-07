"""
Automated E2E Test (No prompts, no pymqi required)
Tests message flow via database inspection.
"""

import sys
import os
from datetime import datetime
import time
import asyncio

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'spbsite'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'spb-shared'))

from spb_shared.models import SPBLocalToBacen, SPBBacenToLocal
from app.database import async_session


async def create_test_message():
    """Create a test message in the database."""
    now = datetime.now()
    nu_ope = now.strftime('%Y%m%d%H%M%S')

    print("=" * 80)
    print("Step 1: Create Test Message")
    print("=" * 80)
    print(f"Operation Number: {nu_ope}")
    print(f"Timestamp: {now}")
    print()

    message = SPBLocalToBacen(
        db_datetime=now,
        cod_msg='SPB0001',
        mq_qn_destino='QR.REQ.36266751.00038166.01',
        status_msg='P',  # Pending
        flag_proc='N',  # Not processed
        nu_ope=nu_ope,
        msg=f'''<?xml version="1.0" encoding="UTF-8"?>
<DOC>
    <BCMSG>
        <IdentdPartDestinat>00038166</IdentdPartDestinat>
        <IdentdPartRemt>36266751</IdentdPartRemt>
        <IdentdOperad>
            <NumCtrl>{nu_ope}</NumCtrl>
            <DtHrOp>{now.strftime('%Y-%m-%dT%H:%M:%S')}</DtHrOp>
        </IdentdOperad>
    </BCMSG>
    <SISMSG>
        <CodMsg>SPB0001</CodMsg>
        <TestMessage>
            <Description>Automated E2E Test</Description>
            <Timestamp>{now.isoformat()}</Timestamp>
        </TestMessage>
    </SISMSG>
</DOC>'''
    )

    async with async_session() as session:
        session.add(message)
        await session.commit()
        await session.refresh(message)

    print("[OK] Message created in database:")
    print(f"   - Operation: {message.nu_ope}")
    print(f"   - Status: {message.status_msg} (P=Pending)")
    print(f"   - Flag: {message.flag_proc} (N=Not Processed)")
    print(f"   - Destination: {message.mq_qn_destino}")
    print()

    return nu_ope


async def check_message_status(nu_ope, check_number=1):
    """Check message status in database."""
    print(f"Check #{check_number}: Message Status")
    print("-" * 80)

    async with async_session() as session:
        from sqlalchemy import select

        # Check outbound message
        result = await session.execute(
            select(SPBLocalToBacen).where(SPBLocalToBacen.nu_ope == nu_ope)
        )
        message = result.scalar_one_or_none()

        if message:
            print(f"[OK] Outbound Message Found:")
            print(f"   - Operation: {message.nu_ope}")
            print(f"   - Status: {message.status_msg}", end="")

            status_desc = {
                'P': 'Pending',
                'E': 'Sent to MQ',
                'C': 'Confirmed',
                'R': 'Rejected'
            }
            print(f" ({status_desc.get(message.status_msg, 'Unknown')})")

            print(f"   - Processed: {message.flag_proc}", end="")
            print(f" ({'Yes' if message.flag_proc == 'S' else 'No'})")

            if message.mq_msg_id:
                print(f"   - MQ Message ID: {message.mq_msg_id.hex()[:16]}...")

            print()

            # Check for responses
            result = await session.execute(
                select(SPBBacenToLocal).where(
                    SPBBacenToLocal.nu_ope.like(f'%{nu_ope}%')
                ).order_by(SPBBacenToLocal.db_datetime.desc())
            )
            responses = result.scalars().all()

            if responses:
                print(f"[OK] {len(responses)} Response(s) Received:")
                for idx, resp in enumerate(responses, 1):
                    print(f"   Response {idx}:")
                    print(f"   - Operation: {resp.nu_ope}")
                    print(f"   - Message Code: {resp.cod_msg}")
                    print(f"   - Status: {resp.status_msg}")
                    print(f"   - Timestamp: {resp.db_datetime}")
                    print()
            else:
                print("[WAIT] No responses received yet")
                print()

            return message
        else:
            print(f"[ERROR] Message not found: {nu_ope}")
            print()
            return None


async def main():
    """Main test function."""
    print("\n")
    print("=" * 80)
    print("SPB E2E Test - Automated")
    print("=" * 80)
    print()

    try:
        # Step 1: Create message
        nu_ope = await create_test_message()

        # Save for later use
        with open('test_scripts/last_operation.txt', 'w') as f:
            f.write(nu_ope)

        # Step 2: Monitor for 30 seconds
        print("=" * 80)
        print("Step 2: Monitor Message Processing (30 seconds)")
        print("=" * 80)
        print()

        checks = 6  # 6 checks × 5 seconds = 30 seconds
        for i in range(checks):
            await check_message_status(nu_ope, i + 1)

            if i < checks - 1:
                print("Waiting 5 seconds...\n")
                await asyncio.sleep(5)

        # Final status
        print("=" * 80)
        print("Test Complete - Final Status")
        print("=" * 80)
        print()

        message = await check_message_status(nu_ope, checks + 1)

        if message:
            if message.flag_proc == 'S':
                print("[OK] SUCCESS: Message was processed by BCSrvSqlMq!")
                print()

                if message.status_msg == 'E':
                    print("[OK] Message was sent to IBM MQ")
                    print()

            else:
                print("[WARN]  Message created but not yet processed")
                print()
                print("Is BCSrvSqlMq running?")
                print("  cd BCSrvSqlMq/python && python -m bcsrvsqlmq.main_srv")
                print()

        print("=" * 80)
        print(f"Operation Number: {nu_ope}")
        print("=" * 80)
        print()
        print("Check in SPBSite: http://localhost:8000")
        print("  Messages → Sent Messages → Search for:", nu_ope)
        print()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

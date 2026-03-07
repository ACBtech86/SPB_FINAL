"""
Simple E2E Test (No pymqi required)
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
        mq_msg_id=b'',
        mq_correl_id=b'',
        status_msg='P',  # Pending
        flag_proc='N',  # Not processed
        mq_qn_origem='',
        mq_qn_destino='QR.REQ.36266751.00038166.01',
        mq_datetime=now,
        mq_header=b'',
        security_header=b'',
        nu_ope=nu_ope,
        cod_msg='SPB0001',
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

    print("✅ Message created in database:")
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
            print(f"✅ Outbound Message Found:")
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

            if message.mq_msg_id and message.mq_msg_id != b'':
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
                print(f"✅ {len(responses)} Response(s) Received:")
                for idx, resp in enumerate(responses, 1):
                    print(f"   Response {idx}:")
                    print(f"   - Operation: {resp.nu_ope}")
                    print(f"   - Message Code: {resp.cod_msg}")
                    print(f"   - Status: {resp.status_msg}")
                    print(f"   - Timestamp: {resp.db_datetime}")
                    print()
            else:
                print("⏳ No responses received yet")
                print()

            return message
        else:
            print(f"❌ Message not found: {nu_ope}")
            print()
            return None


async def main():
    """Main test function."""
    print("\n")
    print("=" * 80)
    print("SPB E2E Test (Simplified - Database Mode)")
    print("=" * 80)
    print()
    print("This test:")
    print("1. Creates a test message in the database")
    print("2. Monitors the message status")
    print("3. Checks for BCSrvSqlMq processing")
    print("4. Looks for response messages")
    print()
    print("Prerequisites:")
    print("- SPBSite database must be accessible")
    print("- BCSrvSqlMq should be running (for full test)")
    print("- IBM MQ should be running (for full test)")
    print()
    input("Press Enter to start the test...")
    print()

    try:
        # Step 1: Create message
        nu_ope = await create_test_message()

        # Save for later use
        with open('test_scripts/last_operation.txt', 'w') as f:
            f.write(nu_ope)

        # Step 2: Wait and check status multiple times
        print("=" * 80)
        print("Step 2: Monitor Message Processing")
        print("=" * 80)
        print()
        print("Waiting for BCSrvSqlMq to process the message...")
        print("(Checking every 5 seconds for 30 seconds)")
        print()

        checks = 6  # 6 checks × 5 seconds = 30 seconds
        for i in range(checks):
            await check_message_status(nu_ope, i + 1)

            if i < checks - 1:
                print("Waiting 5 seconds...\n")
                time.sleep(5)

        # Final status
        print("=" * 80)
        print("Test Complete - Final Status")
        print("=" * 80)
        print()

        message = await check_message_status(nu_ope, checks + 1)

        if message:
            if message.flag_proc == 'S':
                print("✅ SUCCESS: Message was processed by BCSrvSqlMq!")
                print()
                print("Next steps:")
                print("1. Check SPBSite: http://localhost:8000")
                print("2. View message in 'Sent Messages'")
                print("3. Verify in BCSrvSqlMq logs")
                print()

                if message.status_msg == 'E':
                    print("✅ Message was sent to MQ")
                    print()
                    print("To simulate BACEN response (if you have pymqi):")
                    print(f"  python test_scripts/simulate_bacen_response.py -o {nu_ope} -t COA")
                    print()

            else:
                print("⚠️  Message created but not yet processed by BCSrvSqlMq")
                print()
                print("Possible reasons:")
                print("1. BCSrvSqlMq is not running")
                print("2. BCSrvSqlMq polling interval hasn't triggered yet")
                print("3. Database connection issue")
                print()
                print("To manually check:")
                print(f"  SELECT * FROM spb_local_to_bacen WHERE nu_ope = '{nu_ope}';")
                print()

        print("=" * 80)
        print(f"Operation Number: {nu_ope}")
        print("Saved to: test_scripts/last_operation.txt")
        print("=" * 80)
        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

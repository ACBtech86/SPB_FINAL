"""
Submit Test Message to SPBSite
Creates a test message in the database for BCSrvSqlMq to process.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'spbsite'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'spb-shared'))

import asyncio
from spb_shared.models import SPBLocalToBacen
from app.database import async_session


async def submit_test_message():
    """Submit a test message to the database."""

    # Generate operation number
    now = datetime.now()
    nu_ope = now.strftime('%Y%m%d%H%M%S')

    print("=" * 80)
    print("Submit Test Message")
    print("=" * 80)
    print()
    print(f"Operation Number: {nu_ope}")
    print(f"Timestamp: {now}")
    print()

    # Create test message
    message = SPBLocalToBacen(
        db_datetime=now,
        mq_msg_id=b'',  # Will be set by BCSrvSqlMq
        mq_correl_id=b'',
        status_msg='P',  # Pending
        flag_proc='N',  # Not processed
        mq_qn_origem='',
        mq_qn_destino='QR.REQ.36266751.00038166.01',
        mq_datetime=now,
        mq_header=b'',
        security_header=b'',
        nu_ope=nu_ope,
        cod_msg='SPB0001',  # Test message code
        msg=f'''<?xml version="1.0" encoding="UTF-8"?>
<DOC>
    <BCMSG>
        <IdentdPartDestinat>00038166</IdentdPartDestinat>
        <IdentdPartRemt>36266751</IdentdPartRemt>
        <IdentdOperad>
            <NumCtrl>{nu_ope}</NumCtrl>
            <DtHrOp>{now.strftime('%Y-%m-%dT%H:%M:%S')}</DtHrOp>
        </IdentdOperad>
        <Grupo_Seq>
            <NumSeq>1</NumSeq>
        </Grupo_Seq>
    </BCMSG>
    <SISMSG>
        <CodMsg>SPB0001</CodMsg>
        <TestMessage>
            <Field1>Test Value 1</Field1>
            <Field2>Test Value 2</Field2>
            <Timestamp>{now.isoformat()}</Timestamp>
        </TestMessage>
    </SISMSG>
</DOC>'''
    )

    # Save to database
    async with async_session() as session:
        session.add(message)
        await session.commit()
        await session.refresh(message)

    print("✅ Test message created successfully!")
    print()
    print("Message Details:")
    print(f"  - Operation Number: {message.nu_ope}")
    print(f"  - Message Code: {message.cod_msg}")
    print(f"  - Status: {message.status_msg} (Pending)")
    print(f"  - Destination Queue: {message.mq_qn_destino}")
    print()
    print("Next steps:")
    print("1. BCSrvSqlMq should pick up this message automatically")
    print("2. Check BCSrvSqlMq logs for processing")
    print("3. Run: python test_scripts/browse_mq_queue.py QR.REQ.36266751.00038166.01")
    print("4. Run: python test_scripts/simulate_bacen_response.py --operation-number", nu_ope)
    print()

    return nu_ope


def main():
    """Main function."""
    try:
        nu_ope = asyncio.run(submit_test_message())

        # Save operation number to file for other scripts
        with open('test_scripts/last_operation.txt', 'w') as f:
            f.write(nu_ope)

        print(f"✅ Operation number saved to: test_scripts/last_operation.txt")
        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

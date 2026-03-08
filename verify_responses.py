"""Verify BACEN simulator responses in database.

Usage:
    py verify_responses.py
"""

import asyncio
import asyncpg

async def verify():
    conn = await asyncpg.connect(
        user='postgres',
        password='Rama1248',
        host='localhost',
        port=5432,
        database='BCSPB'
    )

    print("\n" + "="*60)
    print("BACEN RESPONSE VERIFICATION")
    print("="*60)

    # Count responses
    count = await conn.fetchval('SELECT COUNT(*) FROM spb_bacen_to_local')
    print(f"\nTotal responses in database: {count}")

    # Get latest responses
    rows = await conn.fetch('''
        SELECT
            nu_ope,
            db_datetime,
            cod_msg,
            status_msg,
            flag_proc,
            mq_qn_origem,
            LEFT(msg, 150) as msg_preview
        FROM spb_bacen_to_local
        ORDER BY db_datetime DESC
        LIMIT 5
    ''')

    print(f"\nLatest {len(rows)} response(s):\n")
    for i, row in enumerate(rows, 1):
        print(f"{i}. Operation: {row['nu_ope']}")
        print(f"   DateTime: {row['db_datetime']}")
        print(f"   Code: {row['cod_msg']}")
        print(f"   Status: {row['status_msg']} | Processed: {row['flag_proc']}")
        print(f"   Queue: {row['mq_qn_origem']}")
        print(f"   XML Preview: {row['msg_preview']}...")
        print()

    await conn.close()
    print("="*60)

if __name__ == '__main__':
    asyncio.run(verify())

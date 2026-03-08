"""Check composite key format in database.

Usage:
    py check_keys.py
"""

import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect(
        user='postgres',
        password='Rama1248',
        host='localhost',
        port=5432,
        database='BCSPB'
    )

    print("\n" + "="*60)
    print("Composite Keys in spb_bacen_to_local")
    print("="*60 + "\n")

    rows = await conn.fetch('''
        SELECT
            db_datetime,
            encode(mq_msg_id, 'hex') as msg_id_hex,
            cod_msg,
            nu_ope
        FROM spb_bacen_to_local
        ORDER BY db_datetime DESC
        LIMIT 5
    ''')

    for i, row in enumerate(rows, 1):
        print(f"Record {i}:")
        print(f"  db_datetime: {row['db_datetime']}")
        print(f"  db_datetime (ISO): {row['db_datetime'].isoformat()}")
        print(f"  mq_msg_id (hex): {row['msg_id_hex']}")
        print(f"  cod_msg: {row['cod_msg']}")
        print(f"  nu_ope: {row['nu_ope']}")

        # Generate composite key in expected format
        composite_key = f"{row['db_datetime'].isoformat()}_{row['msg_id_hex']}"
        print(f"  Composite Key: {composite_key}")
        print()

    await conn.close()

if __name__ == '__main__':
    asyncio.run(check())

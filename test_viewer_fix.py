"""Test that viewer links are generated correctly.

Usage:
    py test_viewer_fix.py
"""

import asyncio
import asyncpg

async def test():
    conn = await asyncpg.connect(
        user='postgres',
        password='Rama1248',
        host='localhost',
        port=5432,
        database='BCSPB'
    )

    print("\n" + "="*60)
    print("Testing Viewer Link Generation")
    print("="*60 + "\n")

    rows = await conn.fetch('''
        SELECT
            db_datetime,
            encode(mq_msg_id, 'hex') as msg_id_hex,
            cod_msg
        FROM spb_bacen_to_local
        ORDER BY db_datetime DESC
        LIMIT 3
    ''')

    for i, row in enumerate(rows, 1):
        dt_str = row['db_datetime'].isoformat()
        msg_id_hex = row['msg_id_hex']
        composite_key = f"{dt_str}_{msg_id_hex}"

        viewer_url = f"/viewer/spb_bacen_to_local/{composite_key}"

        print(f"Message {i}: {row['cod_msg']}")
        print(f"  Composite Key: {composite_key}")
        print(f"  Viewer URL: {viewer_url}")
        print()

    await conn.close()

    print("Testing viewer URL by making a request...")
    print("\nIf SPBSite is running on http://localhost:8000,")
    print("you can test this URL in your browser:")
    if rows:
        test_key = f"{rows[0]['db_datetime'].isoformat()}_{rows[0]['msg_id_hex']}"
        print(f"\nhttp://localhost:8000/viewer/spb_bacen_to_local/{test_key}")

if __name__ == '__main__':
    asyncio.run(test())

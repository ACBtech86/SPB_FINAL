"""Test the composite_key filter with real database data.

Usage:
    py test_filter.py
"""

import asyncio
import asyncpg
from datetime import datetime

# Import the filter
from spbsite.app.templates_config import composite_key_filter

# Create a mock row object
class MockRow:
    def __init__(self, db_datetime, mq_msg_id):
        self.db_datetime = db_datetime
        self.mq_msg_id = mq_msg_id

async def test():
    conn = await asyncpg.connect(
        user='postgres',
        password='Rama1248',
        host='localhost',
        port=5432,
        database='BCSPB'
    )

    print("\n" + "="*60)
    print("Testing composite_key Filter")
    print("="*60 + "\n")

    # Get real data
    rows = await conn.fetch('''
        SELECT
            db_datetime,
            mq_msg_id,
            cod_msg
        FROM spb_bacen_to_local
        ORDER BY db_datetime DESC
        LIMIT 2
    ''')

    for i, row_data in enumerate(rows, 1):
        print(f"Test {i}: {row_data['cod_msg']}")

        # Create mock row
        mock_row = MockRow(
            db_datetime=row_data['db_datetime'],
            mq_msg_id=row_data['mq_msg_id']
        )

        # Test the filter
        try:
            result = composite_key_filter(mock_row)
            print(f"  db_datetime: {mock_row.db_datetime}")
            print(f"  mq_msg_id type: {type(mock_row.mq_msg_id)}")
            print(f"  mq_msg_id: {mock_row.mq_msg_id.hex() if isinstance(mock_row.mq_msg_id, bytes) else 'NOT BYTES'}")
            print(f"  Result: {result[:60]}...")
            print(f"  [SUCCESS]\n")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()
            print()

    await conn.close()

if __name__ == '__main__':
    asyncio.run(test())

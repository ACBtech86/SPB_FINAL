"""Quick test to check if the monitoring endpoint works.

Usage:
    py test_endpoint.py
"""

import asyncio
import sys
sys.path.insert(0, '.')

from app.database import async_session
from app.services.monitoring import get_messages

async def test():
    print("\n" + "="*60)
    print("Testing Monitoring Service")
    print("="*60 + "\n")

    async with async_session() as db:
        try:
            # Call the same function the route uses
            result = await get_messages(db, "inbound", "bacen", limit=5)

            print(f"Title: {result['title']}")
            print(f"Total rows: {len(result['rows'])}")
            print(f"Stats: {result['stats']}")
            print()

            if result['rows']:
                print("First row attributes:")
                row = result['rows'][0]
                print(f"  Type: {type(row)}")
                print(f"  has db_datetime: {hasattr(row, 'db_datetime')}")
                print(f"  has mq_msg_id: {hasattr(row, 'mq_msg_id')}")
                print(f"  cod_msg: {getattr(row, 'cod_msg', 'N/A')}")

                if hasattr(row, 'db_datetime'):
                    print(f"  db_datetime value: {row.db_datetime}")
                if hasattr(row, 'mq_msg_id'):
                    print(f"  mq_msg_id type: {type(row.mq_msg_id)}")
                    print(f"  mq_msg_id value: {row.mq_msg_id}")

                # Test the filter
                from app.templates_config import composite_key_filter
                key = composite_key_filter(row)
                print(f"\n  composite_key result: {key[:60] if key else '[EMPTY]'}...")

            print("\n[SUCCESS] No errors!")

        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test())

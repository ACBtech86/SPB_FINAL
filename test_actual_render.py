#!/usr/bin/env python3
"""Test template rendering with actual SQLAlchemy models."""

import asyncio
import sys
sys.path.insert(0, 'spbsite')

from app.database import async_session
from sqlalchemy import select
from spb_shared.models import SPBBacenToLocal

async def test():
    print("\n" + "="*60)
    print("Testing Template Rendering with Real Data")
    print("="*60 + "\n")

    # Get actual data
    async with async_session() as session:
        result = await session.execute(
            select(SPBBacenToLocal).order_by(SPBBacenToLocal.db_datetime.desc()).limit(2)
        )
        rows = result.scalars().all()

        print(f"Found {len(rows)} rows in database\n")

        if not rows:
            print("No data in spb_bacen_to_local table")
            return

        # Test the filter on each row
        for i, row in enumerate(rows, 1):
            print(f"Row {i}: {row.cod_msg}")
            print(f"  db_datetime: {row.db_datetime}")
            print(f"  db_datetime type: {type(row.db_datetime)}")
            print(f"  mq_msg_id type: {type(row.mq_msg_id)}")

            try:
                # Test the filter directly
                from app.templates_config import composite_key_filter
                composite_key = composite_key_filter(row)
                print(f"  Filter result: {composite_key[:60]}...")
                print(f"  [SUCCESS - Direct call]")

                # Test in Jinja2 context
                from app.templates_config import templates
                template_str = "{{ row | composite_key }}"
                template = templates.env.from_string(template_str)
                rendered = template.render(row=row)
                print(f"  Jinja2 result: {rendered[:60]}...")
                print(f"  [SUCCESS - Jinja2]")

                # Test full URL generation like in template
                table = 'spb_bacen_to_local'
                url = f"/viewer/{table}/{composite_key}"
                print(f"  Generated URL: {url[:80]}...")
                print(f"  [SUCCESS]\n")

            except Exception as e:
                print(f"  [ERROR] {e}")
                import traceback
                traceback.print_exc()
                print()

if __name__ == '__main__':
    asyncio.run(test())

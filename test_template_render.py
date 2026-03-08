#!/usr/bin/env python3
"""Test template rendering with composite_key filter."""

import asyncio
import sys
sys.path.insert(0, 'spbsite')

from app.templates_config import templates
from app.database import get_db_engine, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from spb_shared.models import SPBBacenToLocal

async def test():
    print("\n" + "="*60)
    print("Testing Template Rendering with composite_key Filter")
    print("="*60 + "\n")

    # Create database engine and session
    engine = get_db_engine()
    async with get_async_session(engine) as session:
        # Get actual data
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
            print(f"Row {i}:")
            print(f"  cod_msg: {row.cod_msg}")
            print(f"  db_datetime: {row.db_datetime}")
            print(f"  mq_msg_id type: {type(row.mq_msg_id)}")

            try:
                # Test the filter
                from app.templates_config import composite_key_filter
                composite_key = composite_key_filter(row)
                print(f"  composite_key: {composite_key[:60]}...")
                print(f"  [SUCCESS]\n")

                # Test in Jinja2 context
                template_str = "{{ row | composite_key }}"
                template = templates.env.from_string(template_str)
                rendered = template.render(row=row)
                print(f"  Jinja2 rendered: {rendered[:60]}...")
                print(f"  [SUCCESS - Jinja2]\n")

            except Exception as e:
                print(f"  [ERROR] {e}")
                import traceback
                traceback.print_exc()
                print()

    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(test())

"""Shared Jinja2 templates configuration with custom filters."""

from pathlib import Path
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent

# Shared Jinja2 templates instance
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# Custom Jinja2 filters
def composite_key_filter(row):
    """Generate composite key for message tables with (db_datetime, mq_msg_id) PK.

    Args:
        row: SQLAlchemy model instance with db_datetime and mq_msg_id attributes

    Returns:
        str: Composite key in format "{datetime_iso}_{mq_msg_id_hex}"
    """
    try:
        if not hasattr(row, 'db_datetime'):
            print(f"[WARNING] Row has no db_datetime attribute: {type(row)}")
            return ""
        if not hasattr(row, 'mq_msg_id'):
            print(f"[WARNING] Row has no mq_msg_id attribute: {type(row)}")
            return ""

        if row.db_datetime is None:
            print(f"[WARNING] Row db_datetime is None")
            return ""
        if row.mq_msg_id is None:
            print(f"[WARNING] Row mq_msg_id is None")
            return ""

        dt_str = row.db_datetime.isoformat()
        msg_id_hex = row.mq_msg_id.hex()
        result = f"{dt_str}_{msg_id_hex}"
        return result
    except Exception as e:
        print(f"[ERROR] composite_key_filter failed: {e}")
        import traceback
        traceback.print_exc()
        return ""


# Register custom filters
templates.env.filters["composite_key"] = composite_key_filter

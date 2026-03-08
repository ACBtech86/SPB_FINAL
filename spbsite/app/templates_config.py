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
    if hasattr(row, 'db_datetime') and hasattr(row, 'mq_msg_id'):
        if row.db_datetime and row.mq_msg_id:
            dt_str = row.db_datetime.isoformat()
            msg_id_hex = row.mq_msg_id.hex()
            return f"{dt_str}_{msg_id_hex}"
    return ""


# Register custom filters
templates.env.filters["composite_key"] = composite_key_filter

"""Operation number generator.

Replaces the SPB.SPBXML COM component's Gera_Num_Ope() method.
The operation number format is: ISPB + datetime + sequence.
"""

import threading
from datetime import datetime

from app.config import settings

_lock = threading.Lock()
_sequence = 0


def generate_operation_number() -> str:
    """Generate a unique SPB operation number.

    Format: ISPB_LOCAL (8 chars) + YYYYMMDD (8 chars) + sequence (7 chars zero-padded)
    Total: 23 characters
    """
    global _sequence
    with _lock:
        _sequence += 1
        seq = _sequence

    now = datetime.now()
    date_part = now.strftime("%Y%m%d")
    seq_part = f"{seq:07d}"

    return f"{settings.ispb_local}{date_part}{seq_part}"

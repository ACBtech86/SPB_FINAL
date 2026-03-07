"""SQLAlchemy models for SPB system."""

from spb_shared.models.auth import User
from spb_shared.models.catalog import SPBDicionario, SPBMensagem, SPBMsgField, SPBXmlXsl
from spb_shared.models.control import BacenControle, SPBControle
from spb_shared.models.logs import SPBLogBacen, SPBLogSelic
from spb_shared.models.messages import (
    SPBBacenToLocal,
    SPBLocalToBacen,
    SPBLocalToSelic,
    SPBSelicToLocal,
)
from spb_shared.models.queue import Camaras, Fila

__all__ = [
    # Auth
    "User",
    # Control
    "SPBControle",
    "BacenControle",
    # Messages
    "SPBBacenToLocal",
    "SPBSelicToLocal",
    "SPBLocalToBacen",
    "SPBLocalToSelic",
    # Logs
    "SPBLogBacen",
    "SPBLogSelic",
    # Catalog
    "SPBMensagem",
    "SPBMsgField",
    "SPBDicionario",
    "SPBXmlXsl",
    # Queue
    "Fila",
    "Camaras",
]

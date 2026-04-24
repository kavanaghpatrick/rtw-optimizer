"""Area: live RTW trip state persisted in SQLite.

Stores a current (and optional historical) itinerary under active booking,
allowing segments to be added, moved, and removed while preserving order.
"""

from rtw.area.db import default_db_path, open_area_db
from rtw.area.repo import AreaRepo, NoActiveTripError, TripNotFoundError

__all__ = [
    "AreaRepo",
    "NoActiveTripError",
    "TripNotFoundError",
    "default_db_path",
    "open_area_db",
]

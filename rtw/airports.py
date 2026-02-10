"""Shared airportsdata loader with fail-fast.

Loads the airportsdata IATA database exactly once at import time.
All consumer modules should import from here instead of loading
airportsdata directly.

If airportsdata is not installed, exits immediately with code 2
and a clear error message — without it, distances become 0,
continents become None, and every downstream calculation is wrong.
"""

import sys

try:
    import airportsdata

    airports_db: dict = airportsdata.load("IATA")
except ImportError:
    try:
        from rich.console import Console
        from rich.panel import Panel

        console = Console(stderr=True)
        console.print(
            Panel(
                "Required library 'airportsdata' is not available.\n\n"
                "Fix: pip install airportsdata",
                title="Missing Dependency",
                border_style="red",
            )
        )
    except ImportError:
        print(
            "Error: Required library 'airportsdata' is not available.\n"
            "Fix: pip install airportsdata",
            file=sys.stderr,
        )
    sys.exit(2)

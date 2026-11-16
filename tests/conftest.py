"""Shared test fixtures for RTW Optimizer."""

import yaml
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def _no_live_serpapi(monkeypatch):
    # The suite must never spend real SerpAPI credits or stall on the
    # live service; tests that need the key set it explicitly.
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)


@pytest.fixture
def load_yaml():
    """Return a function that loads a YAML fixture file."""

    def _load(name: str) -> dict:
        path = FIXTURES_DIR / name
        with open(path) as f:
            return yaml.safe_load(f)

    return _load


@pytest.fixture
def v3_itinerary(load_yaml):
    """Load the V3 reference routing."""
    return load_yaml("valid_v3.yaml")


@pytest.fixture
def v3_same_city_itinerary(load_yaml):
    """Original V3 with NRT->HND and TSA->TPE airport changes (18 segments, invalid)."""
    return load_yaml("v3_same_city_gaps.yaml")


@pytest.fixture
def qr_first_itinerary(load_yaml):
    """Load the invalid QR-first routing."""
    return load_yaml("invalid_qr_first.yaml")


@pytest.fixture
def hawaii_backtrack_itinerary(load_yaml):
    """Load the invalid Hawaii backtracking routing."""
    return load_yaml("invalid_hawaii_backtrack.yaml")


@pytest.fixture
def too_many_segments_itinerary(load_yaml):
    """Load the invalid 17-segment routing."""
    return load_yaml("invalid_too_many_segments.yaml")


@pytest.fixture
def minimal_valid_itinerary(load_yaml):
    """Load the minimal valid routing."""
    return load_yaml("minimal_valid.yaml")


@pytest.fixture
def done3_itinerary(load_yaml):
    """Load the DONE3 business 3-continent routing."""
    return load_yaml("done3_cai_eastbound.yaml")


@pytest.fixture
def lone3_itinerary(load_yaml):
    """Load the LONE3 economy 3-continent routing."""
    return load_yaml("lone3_osl_westbound.yaml")

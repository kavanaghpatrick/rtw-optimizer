"""Pydantic models for nonstop route pre-verification."""

import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NonstopAlternative(BaseModel):
    """A oneworld carrier with nonstop service on a route."""

    carrier: str = Field(min_length=2, max_length=2)
    carrier_name: str
    has_nonstop: bool
    nonstop_flight_count: int = Field(default=0, ge=0)
    price_range_usd: Optional[tuple[float, float]] = None


class NonstopResult(BaseModel):
    """Result of a nonstop check for a single origin-dest-carrier."""

    origin: str = Field(min_length=3, max_length=3)
    destination: str = Field(min_length=3, max_length=3)
    carrier: str = Field(min_length=2, max_length=2)
    carrier_name: str
    date_checked: datetime.date
    has_nonstop: bool
    nonstop_flight_count: int = Field(default=0, ge=0)
    from_cache: bool = False
    source: str = "serpapi"
    price_range_usd: Optional[tuple[float, float]] = None
    alternatives: list[NonstopAlternative] = Field(default_factory=list)
    error: Optional[str] = None

    @property
    def nonstop_alternatives(self) -> list[NonstopAlternative]:
        """Alternatives that have confirmed nonstop service."""
        return [a for a in self.alternatives if a.has_nonstop]


class NonstopSegmentResult(BaseModel):
    """A segment result within a batch check."""

    index: int = Field(ge=0)
    origin: str = Field(min_length=3, max_length=3)
    destination: str = Field(min_length=3, max_length=3)
    carrier: str = Field(min_length=2, max_length=2)
    result: Optional[NonstopResult] = None


class NonstopBatchResult(BaseModel):
    """Aggregated result of a batch nonstop check."""

    segments: list[NonstopSegmentResult] = Field(default_factory=list)
    date_checked: datetime.date
    total: int = Field(ge=0)
    nonstop_count: int = Field(default=0, ge=0)
    no_nonstop_count: int = Field(default=0, ge=0)
    error_count: int = Field(default=0, ge=0)
    api_calls_used: int = Field(default=0, ge=0)

    @property
    def all_clear(self) -> bool:
        """True when all segments have nonstop service and no errors."""
        return self.no_nonstop_count == 0 and self.error_count == 0

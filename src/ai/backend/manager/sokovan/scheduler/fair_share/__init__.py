"""Fair share calculation module for the Sokovan scheduler.

This module provides components for tracking kernel resource usage
and calculating fair share scheduling ranks.
"""

from .aggregator import FairShareAggregator

__all__ = [
    "FairShareAggregator",
]

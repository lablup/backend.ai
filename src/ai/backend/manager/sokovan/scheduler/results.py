"""
Result type for scheduling operations.
"""

from dataclasses import dataclass


@dataclass
class ScheduleResult:
    """Result of a scheduling operation."""

    succeeded_count: int = 0

    def needs_post_processing(self) -> bool:
        """Check if post-processing is needed based on the result."""
        return self.succeeded_count > 0

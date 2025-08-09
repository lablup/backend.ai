from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class QueryData:
    query: str
    start: Optional[str]
    end: Optional[str]
    step: Optional[str]


@dataclass
class QueryRange:
    step: str
    start: Optional[datetime]
    end: Optional[datetime]

    @property
    def start_iso(self) -> Optional[str]:
        return self.start.isoformat() if self.start else None

    @property
    def end_iso(self) -> Optional[str]:
        return self.end.isoformat() if self.end else None


@dataclass
class QueryStringSpec:
    metric_name: Optional[str]
    timewindow: str
    sum_by: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)

    def str_sum_by(self) -> str:
        if not self.sum_by:
            return ""
        return f"sum by ({','.join(self.sum_by)})"

    def str_labels(self) -> str:
        if not self.labels:
            return ""
        return f"{{{','.join(self.labels)}}}"

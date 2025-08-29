import dataclasses
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from ai.backend.manager.data.session.types import SessionStatus


@dataclass
class LegacySessionInfo:
    """
    Deprecated.
    Only use this type in `GetSessionInfo` Action.
    """

    age_ms: int = field(compare=False)
    domain_name: str
    group_id: UUID
    user_id: UUID
    lang: str
    image: str
    architecture: str
    registry: Optional[str]
    tag: Optional[str]
    container_id: UUID
    occupied_slots: str  # legacy
    occupying_slots: str
    requested_slots: str
    occupied_shares: str  # legacy
    environ: str
    resource_opts: str
    status: SessionStatus
    status_info: Optional[str]
    status_data: Optional[dict[str, Any]]
    creation_time: datetime
    termination_time: Optional[datetime]
    num_queries_executed: int
    last_stat: Optional[dict[str, Any]]
    idle_checks: Any

    def asdict(self) -> dict[str, Any]:
        """
        Return a dict whose keys exactly match the old `resp` payload.
        """
        return {
            "age": self.age_ms,
            "domainName": self.domain_name,
            "groupId": str(self.group_id),
            "userId": str(self.user_id),
            "lang": self.lang,
            "image": self.image,
            "architecture": self.architecture,
            "registry": self.registry,
            "tag": self.tag,
            "containerId": str(self.container_id),
            "occupiedSlots": self.occupied_slots,
            "occupyingSlots": self.occupying_slots,
            "requestedSlots": self.requested_slots,
            "occupiedShares": self.occupied_shares,
            "environ": self.environ,
            "resourceOpts": self.resource_opts,
            "status": self.status.name,  # Enum → its name (e.g. "RUNNING")
            "statusInfo": self.status_info or "None",  # legacy
            "statusData": self.status_data,
            "creationTime": self.creation_time.isoformat(),
            "terminationTime": (
                self.termination_time.isoformat() if self.termination_time else None
            ),
            "numQueriesExecuted": self.num_queries_executed,
            "lastStat": self.last_stat,
            "idleChecks": self.idle_checks,
        }


@dataclass
class CommitStatusInfo:
    status: str
    kernel: str

    def asdict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

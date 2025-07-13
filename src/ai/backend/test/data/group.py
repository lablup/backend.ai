from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CreatedGroupMeta:
    group_id: UUID
    group_name: str

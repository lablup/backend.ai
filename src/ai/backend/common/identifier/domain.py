import uuid
from typing import NewType

__all__ = (
    "DomainID",
    "DomainName",
)


DomainID = NewType("DomainID", uuid.UUID)
DomainName = NewType("DomainName", str)

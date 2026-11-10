"""Internal read-projections of a session template for the template service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.backend.common.identifier.user import UserID


@dataclass
class ClusterTemplateWithOwnerAndDomain:
    template: dict[str, Any]
    owner_id: UserID
    domain_name: str

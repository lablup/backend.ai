from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Final, Protocol

import sqlalchemy as sa

from ai.backend.common.cc_storage import (
    CAPABILITY_HEADER,
    CONCURRENT_TIER,
    FORMAT_ID,
    TAMPER_EVIDENT,
    TIER_DISCLOSURE,
    FolderKeyMaterial,
)
from ai.backend.manager.confidential.storage import FolderKeyCustodian
from ai.backend.manager.errors.confidential import ClientFormatRefused, ReleaseDenied
from ai.backend.manager.models.confidential.row import ConfidentialClientReleaseRow
from ai.backend.manager.models.scaling_group.row import (
    ScalingGroupForDomainRow,
    ScalingGroupRow,
)
from ai.backend.manager.models.scaling_group.types import ConfidentialScalingGroupOpts
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

CLIENT_TRUST_STATEMENT: Final = (
    "A client cannot attest. This release is authorised by the caller's Backend.AI credentials and"
    " the folder grant alone, never by a hardware-signed measurement, so this leg of confidential"
    " storage is weaker than the attested-guest leg beside it and no parity between them is claimed."
    " The manager cannot distinguish a genuine client from any software holding the same credentials"
    " on the same device, and it cannot tell what that device does with the key afterwards. The"
    " format is symmetric, so a read-only grant is not cryptographically enforced: every device ever"
    " granted read access holds a key that also writes. Revoking a grant does not revoke the key, and"
    " version one has no re-key operation, so the exposure of a leaked client device is every byte"
    " the folder ever holds. This is the same key the attested guest holds, because a folder has"
    " exactly one, so that exposure covers what a confidential session writes as well as what a"
    " client uploads."
)

RELEASE_TTL: Final = timedelta(hours=12)


class FolderKeyCustody(Protocol):
    async def material(
        self,
        opts: ConfidentialScalingGroupOpts,
        domain_name: str,
        vfolder_id: uuid.UUID,
        tier: str,
    ) -> FolderKeyMaterial: ...


class CustodianFolderKeyCustody:
    def __init__(self, custodian: FolderKeyCustodian) -> None:
        self._custodian = custodian

    async def material(
        self,
        opts: ConfidentialScalingGroupOpts,
        domain_name: str,
        vfolder_id: uuid.UUID,
        tier: str,
    ) -> FolderKeyMaterial:
        return FolderKeyMaterial(
            key=self._custodian.release(opts, domain_name, vfolder_id), tier=tier
        )


@dataclass(frozen=True)
class ClientRelease:
    material: FolderKeyMaterial
    scope: str
    expires_at: datetime

    def to_json(self) -> dict[str, Any]:
        tier = self.material.tier if self.material.tier in TAMPER_EVIDENT else CONCURRENT_TIER
        return {
            "format": FORMAT_ID,
            **self.material.to_json(),
            "tamper_evident": TAMPER_EVIDENT[tier],
            "tier_disclosure": TIER_DISCLOSURE[tier],
            "scope": self.scope,
            "expires_at": self.expires_at.isoformat(),
            "trust": CLIENT_TRUST_STATEMENT,
        }


class ClientKeyRelease:
    def __init__(self, db: ExtendedAsyncSAEngine, custody: FolderKeyCustody) -> None:
        self._db = db
        self._custody = custody

    async def opts_for_domain(self, domain_name: str) -> ConfidentialScalingGroupOpts:
        async with self._db.begin_readonly_session() as db_session:
            rows = (
                await db_session.scalars(
                    sa.select(ScalingGroupRow)
                    .join(
                        ScalingGroupForDomainRow,
                        ScalingGroupForDomainRow.scaling_group == ScalingGroupRow.name,
                    )
                    .where(ScalingGroupForDomainRow.domain == domain_name)
                )
            ).all()
        confidential = [row.confidential for row in rows if row.confidential.enabled]
        if len(confidential) != 1:
            raise ReleaseDenied(
                extra_msg=(
                    f"domain {domain_name} is served by {len(confidential)} confidential scaling"
                    " groups; a tenant is a domain and must have exactly one"
                )
            )
        return confidential[0]

    async def release(
        self,
        *,
        domain_name: str,
        vfolder_id: uuid.UUID,
        tier: str,
        requester_id: uuid.UUID,
        requester: str,
        session_id: uuid.UUID | None,
        declared_format: str | None,
    ) -> ClientRelease:
        if declared_format != FORMAT_ID:
            raise ClientFormatRefused(
                extra_msg=(
                    f"the caller declared {declared_format!r} in {CAPABILITY_HEADER};"
                    f" {FORMAT_ID} is required to hold a key for an encrypted folder"
                )
            )
        opts = await self.opts_for_domain(domain_name)
        material = await self._custody.material(opts, domain_name, vfolder_id, tier)
        scope = f"session:{session_id}" if session_id is not None else "client"
        expires_at = datetime.now(UTC) + RELEASE_TTL
        async with self._db.begin_session() as db_session:
            db_session.add(
                ConfidentialClientReleaseRow(
                    vfolder_id=vfolder_id,
                    domain_name=domain_name,
                    requester_id=requester_id,
                    requester=requester,
                    session_id=session_id,
                    scope=scope,
                    tier=material.tier,
                    expires_at=expires_at,
                )
            )
        return ClientRelease(material=material, scope=scope, expires_at=expires_at)


def enforce_client_format(headers: Any, folder_row: Any, writing: bool) -> None:
    if not writing or getattr(folder_row, "encryption_tier", None) is None:
        return
    declared = headers.get(CAPABILITY_HEADER)
    if declared != FORMAT_ID:
        raise ClientFormatRefused(
            extra_msg=(
                f"this client declared {declared!r} in {CAPABILITY_HEADER} and would write"
                f" plaintext into an encrypted folder; {FORMAT_ID} is required"
            )
        )

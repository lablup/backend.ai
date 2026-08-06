from __future__ import annotations

import json
import re
import secrets
import uuid
from datetime import UTC, datetime
from typing import Final

import sqlalchemy as sa
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.manager.errors.confidential import (
    LaunchCredentialRefused,
    LaunchCredentialRequired,
)
from ai.backend.manager.models.confidential.row import ConfidentialLaunchCredentialRow
from ai.backend.manager.models.scaling_group.types import ConfidentialScalingGroupOpts
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, execute_with_txn_retry

LAUNCH_CREDENTIAL_CONTEXT: Final = b"backend.ai confidential launch credential v1\n"
LAUNCH_NONCE_SHAPE: Final = re.compile(r"\A[A-Za-z0-9_-]{16,128}\Z")


def credential_statement(nonce: str, domain_name: str, image_digest: str, quota: int) -> bytes:
    return LAUNCH_CREDENTIAL_CONTEXT + json.dumps(
        {
            "domain_name": domain_name,
            "image_digest": image_digest,
            "nonce": nonce,
            "quota": quota,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


class LaunchAuthority:
    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def deposit(
        self,
        opts: ConfidentialScalingGroupOpts,
        *,
        nonce: str,
        domain_name: str,
        image_digest: str,
        quota: int,
        signature: str,
    ) -> None:
        if not opts.launch_authority_public_key:
            raise LaunchCredentialRefused(
                extra_msg=(
                    "this scaling group names no tenant launch authority, so the manager mints"
                    " its own launch nonces and a deposited credential would gate nothing"
                )
            )
        if LAUNCH_NONCE_SHAPE.fullmatch(nonce) is None:
            raise LaunchCredentialRefused(
                extra_msg=(
                    "a launch nonce is 16 to 128 characters of the URL-safe alphabet, because it"
                    " is carried as one dot-separated half of a broker resource path segment"
                )
            )
        try:
            Ed25519PublicKey.from_public_bytes(
                bytes.fromhex(opts.launch_authority_public_key)
            ).verify(
                bytes.fromhex(signature),
                credential_statement(nonce, domain_name, image_digest, quota),
            )
        except (ValueError, InvalidSignature) as e:
            raise LaunchCredentialRefused(
                extra_msg=f"the tenant launch authority did not sign this credential: {e}"
            )
        async with self._db.begin_session() as db_session:
            seen = await db_session.scalar(
                sa.select(ConfidentialLaunchCredentialRow.nonce).where(
                    ConfidentialLaunchCredentialRow.nonce == nonce
                )
            )
            if seen is not None:
                raise LaunchCredentialRefused(
                    extra_msg=(
                        "this launch credential was deposited before; a credential is single use"
                        " and depositing it again does not restore it"
                    )
                )
            db_session.add(
                ConfidentialLaunchCredentialRow(
                    nonce=nonce,
                    endpoint=opts.broker_endpoint,
                    domain_name=domain_name,
                    image_digest=image_digest,
                    quota=quota,
                    signature=signature,
                )
            )

    async def mint(
        self,
        opts: ConfidentialScalingGroupOpts,
        *,
        session_id: uuid.UUID,
        domain_name: str,
        image_digest: str,
        quota: int,
    ) -> str:
        if not opts.launch_authority_public_key:
            return secrets.token_urlsafe(24)

        async def _spend(db_session: SASession) -> str:
            row = await db_session.scalar(
                sa.select(ConfidentialLaunchCredentialRow)
                .where(
                    (ConfidentialLaunchCredentialRow.endpoint == opts.broker_endpoint)
                    & (ConfidentialLaunchCredentialRow.domain_name == domain_name)
                    & (ConfidentialLaunchCredentialRow.image_digest == image_digest)
                    & (ConfidentialLaunchCredentialRow.quota == quota)
                    & ConfidentialLaunchCredentialRow.spent_at.is_(None)
                )
                .order_by(ConfidentialLaunchCredentialRow.deposited_at)
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            if row is None:
                raise LaunchCredentialRequired(
                    extra_msg=(
                        f"no unspent launch credential signed by the tenant launch authority of"
                        f" {opts.broker_endpoint} covers image {image_digest} at {quota} members"
                        f" in domain {domain_name}"
                    )
                )
            row.spent_at = datetime.now(UTC)
            row.session_id = session_id
            return row.nonce

        async with self._db.connect() as conn:
            return await execute_with_txn_retry(_spend, self._db.begin_session, conn)

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from http.cookies import SimpleCookie
from typing import Any, Final, NamedTuple

import sqlalchemy as sa
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.confidential.broker import BrokerClient, BrokerTarget
from ai.backend.manager.confidential.payloads import TIME_RESOURCE
from ai.backend.manager.confidential.storage import FOLDER_KEY_SEGMENT, folder_key_tag
from ai.backend.manager.errors.confidential import (
    BrokerUnreachable,
    FolderKeyNotEntitled,
    NonceQuotaExhausted,
    ReferenceValueRejected,
    ShimRefusal,
)
from ai.backend.manager.metrics.confidential import ConfidentialMetricObserver
from ai.backend.manager.models.confidential.row import (
    ConfidentialAttestedGuestRow,
    ConfidentialDecisionRow,
    ConfidentialGuestClaimRow,
    ConfidentialNonceRow,
    ConfidentialReferenceValueRow,
    ConfidentialSessionResourceRow,
)
from ai.backend.manager.models.confidential.types import (
    DecisionActor,
    DecisionVerdict,
    ReferenceValueState,
    SessionResourceKind,
)
from ai.backend.manager.models.scaling_group.types import ConfidentialScalingGroupOpts
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, execute_with_txn_retry

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

RCAR_SESSION_COOKIE: Final = "kbs-session-id"
RELAYED_REQUEST_HEADERS: Final = frozenset({
    "content-type",
    "accept",
    "user-agent",
    "cookie",
    "authorization",
})
RELAYED_RESPONSE_HEADERS: Final = frozenset({"content-type", "set-cookie", "www-authenticate"})
UNDATED_CLAIM_LEASE: Final = timedelta(minutes=5)

_QUOTE_HEADER_LEN: Final = 48
_MR_TD: Final = slice(136, 184)
_MR_CONFIG_ID: Final = slice(184, 232)
_RTMR_1: Final = slice(376, 424)
_RTMR_2: Final = slice(424, 472)


def _report_body(evidence: Any) -> bytes | None:
    stack = [evidence]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            quote = node.get("quote")
            if isinstance(quote, str):
                try:
                    raw = base64.b64decode(quote, validate=False)
                except binascii.Error:
                    raw = b""
                if len(raw) >= _QUOTE_HEADER_LEN + 584:
                    return raw[_QUOTE_HEADER_LEN : _QUOTE_HEADER_LEN + 584]
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return None


def path_nonce(resource_path: str) -> str | None:
    segments = resource_path.split("/")
    if len(segments) != 3:
        return None
    return segments[1].partition(".")[2] or None


def folder_key_subject(resource_path: str) -> tuple[str, uuid.UUID] | None:
    segments = resource_path.split("/")
    if len(segments) != 3 or segments[1] != FOLDER_KEY_SEGMENT:
        return None
    try:
        return segments[0], uuid.UUID(segments[2])
    except ValueError:
        return None


def _tee_pubkey(claims: Any) -> Any:
    stack = [claims]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            found = node.get("tee-pubkey")
            if found is not None:
                return found
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return None


def _pubkey_digest(pubkey: Any) -> str:
    rendered = json.dumps(pubkey, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(rendered).hexdigest()


class Claimant(NamedTuple):
    guest: str
    expires_at: datetime


def _token_expiry(claims: Any) -> datetime:
    moment = claims.get("exp") if isinstance(claims, dict) else None
    if not isinstance(moment, (int, float)) or isinstance(moment, bool):
        return datetime.now(UTC) + UNDATED_CLAIM_LEASE
    return datetime.fromtimestamp(moment, UTC)


def attested_guest(headers: dict[str, str]) -> Claimant | None:
    for key, value in headers.items():
        if key.lower() != "authorization":
            continue
        scheme, _, token = value.partition(" ")
        if scheme.lower() != "bearer":
            continue
        segments = token.split(".")
        if len(segments) < 2:
            continue
        payload = segments[1] + "=" * (-len(segments[1]) % 4)
        try:
            claims = json.loads(base64.urlsafe_b64decode(payload))
        except (ValueError, binascii.Error):
            continue
        pubkey = _tee_pubkey(claims)
        if pubkey is None:
            continue
        return Claimant(_pubkey_digest(pubkey), _token_expiry(claims))
    return None


def presented_guest(evidence: Any) -> str | None:
    pubkey = _tee_pubkey(evidence)
    return None if pubkey is None else _pubkey_digest(pubkey)


def rcar_session(headers: dict[str, str]) -> str | None:
    jar: SimpleCookie = SimpleCookie()
    for key, value in headers.items():
        if key.lower() == "cookie":
            jar.load(value)
    morsel = jar.get(RCAR_SESSION_COOKIE)
    return morsel.value if morsel is not None else None


def presented_registers(body: bytes | None) -> dict[str, str] | None:
    if body is None:
        return None
    return {
        "mr_td": body[_MR_TD].hex(),
        "mr_config_id": body[_MR_CONFIG_ID].hex(),
        "rtmr_1": body[_RTMR_1].hex(),
        "rtmr_2": body[_RTMR_2].hex(),
    }


def admits(measurements: dict[str, Any], registers: dict[str, str]) -> bool:
    pinned = 0
    for field, presented in registers.items():
        expected = measurements.get(field)
        if not expected:
            continue
        admitted = expected if isinstance(expected, list) else [expected]
        if presented not in admitted:
            return False
        pinned += 1
    return pinned == len(registers)


class AuthorisationShim:
    def __init__(self, db: ExtendedAsyncSAEngine, broker: BrokerClient) -> None:
        self._db = db
        self._broker = broker

    async def record(
        self,
        *,
        actor: DecisionActor,
        verdict: DecisionVerdict,
        resource_path: str,
        measurement: str | None = None,
        failing_clause: str | None = None,
        session_id: uuid.UUID | None = None,
        nonce: str | None = None,
        db_session: SASession | None = None,
    ) -> None:
        row = ConfidentialDecisionRow(
            actor=actor,
            verdict=verdict,
            resource_path=resource_path,
            measurement=measurement,
            failing_clause=failing_clause,
            session_id=session_id,
            nonce=nonce,
        )
        if db_session is not None:
            db_session.add(row)
        else:
            async with self._db.begin_session() as own_session:
                own_session.add(row)
        ConfidentialMetricObserver.instance().observe_decision(actor, verdict)

    async def authorise_session_path(
        self, domain_name: str, session_id: uuid.UUID, nonce: str, resource_path: str
    ) -> str:
        expected_prefix = f"{domain_name}/{session_id}.{nonce}/"
        tail = resource_path.removeprefix(expected_prefix)
        refusal: str | None = None
        if not resource_path.startswith(expected_prefix):
            refusal = f"path is not under the session's domain scope {expected_prefix}"
        elif not tail or "/" in tail or ".." in tail:
            refusal = "path must carry exactly one tag segment under the session scope"
        if refusal is not None:
            await self.record(
                actor=DecisionActor.MANAGER,
                verdict=DecisionVerdict.OUT_OF_SCOPE,
                resource_path=resource_path,
                failing_clause=refusal,
                session_id=session_id,
            )
            raise ShimRefusal(extra_msg=refusal)
        return resource_path

    async def authorise_bundle(
        self, opts: ConfidentialScalingGroupOpts, kind: str, bundle: bytes, signature: str
    ) -> None:
        refusal: str | None = None
        if not opts.pipeline_public_key:
            refusal = "no deterministic build pipeline public key is configured"
        else:
            try:
                key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(opts.pipeline_public_key))
                key.verify(bytes.fromhex(signature), bundle)
            except (ValueError, InvalidSignature) as e:
                refusal = f"pipeline signature did not verify: {e}"
        if refusal is not None:
            await self.record(
                actor=DecisionActor.MANAGER,
                verdict=DecisionVerdict.OUT_OF_SCOPE,
                resource_path=f"{kind}-bundle",
                failing_clause=refusal,
            )
            raise ReferenceValueRejected(extra_msg=refusal)

    async def _release_claim(self, nonce: str, guest: str) -> None:
        async def _drop(db_session: SASession) -> None:
            await db_session.execute(
                sa.delete(ConfidentialGuestClaimRow).where(
                    (ConfidentialGuestClaimRow.nonce == nonce)
                    & (ConfidentialGuestClaimRow.guest == guest)
                )
            )

        async with self._db.connect() as conn:
            await execute_with_txn_retry(_drop, self._db.begin_session, conn)

    async def _consume(self, nonce: str, claimant: Claimant) -> tuple[uuid.UUID, bool]:
        async def _claim(db_session: SASession) -> tuple[uuid.UUID, bool]:
            bound = await db_session.scalar(
                sa.select(ConfidentialNonceRow)
                .where(ConfidentialNonceRow.nonce == nonce)
                .with_for_update()
            )
            if bound is None:
                raise NonceQuotaExhausted(
                    extra_msg=(
                        "no session nonce of this name is provisioned, so the session that"
                        " carried it has had its confidential resources destroyed"
                    )
                )
            if bound.reference_value_id is None:
                bound.reference_value_id = await db_session.scalar(
                    sa.select(ConfidentialAttestedGuestRow.reference_value_id).where(
                        (ConfidentialAttestedGuestRow.guest == claimant.guest)
                        & (ConfidentialAttestedGuestRow.endpoint == bound.endpoint)
                    )
                )
            held = await db_session.scalar(
                sa.select(ConfidentialGuestClaimRow).where(
                    (ConfidentialGuestClaimRow.nonce == nonce)
                    & (ConfidentialGuestClaimRow.guest == claimant.guest)
                )
            )
            if held is not None:
                held.expires_at = claimant.expires_at
                return bound.session_id, False
            live = await db_session.scalar(
                sa.select(sa.func.count())
                .select_from(ConfidentialGuestClaimRow)
                .where(
                    (ConfidentialGuestClaimRow.nonce == nonce)
                    & (ConfidentialGuestClaimRow.expires_at > sa.func.now())
                )
            )
            if live < bound.quota:
                db_session.add(
                    ConfidentialGuestClaimRow(
                        nonce=nonce,
                        guest=claimant.guest,
                        session_id=bound.session_id,
                        expires_at=claimant.expires_at,
                    )
                )
                return bound.session_id, True
            raise NonceQuotaExhausted(extra_msg="no live claim slot remains for this session nonce")

        async with self._db.connect() as conn:
            return await execute_with_txn_retry(_claim, self._db.begin_session, conn)

    async def _entitling_session(
        self, guest: str, domain_name: str, folder_id: uuid.UUID
    ) -> uuid.UUID | None:
        async with self._db.begin_readonly_session() as db_session:
            return await db_session.scalar(
                sa.select(ConfidentialSessionResourceRow.session_id)
                .join(
                    ConfidentialGuestClaimRow,
                    ConfidentialGuestClaimRow.session_id
                    == ConfidentialSessionResourceRow.session_id,
                )
                .where(
                    (ConfidentialGuestClaimRow.guest == guest)
                    & (ConfidentialGuestClaimRow.expires_at > sa.func.now())
                    & (ConfidentialSessionResourceRow.kind == SessionResourceKind.FOLDER_KEY)
                    & ConfidentialSessionResourceRow.deleted_at.is_(None)
                    & ConfidentialSessionResourceRow.resource_path.startswith(f"{domain_name}/")
                    & ConfidentialSessionResourceRow.resource_path.endswith(
                        f"/{folder_key_tag(folder_id)}"
                    )
                )
            )

    async def _authorise_unscoped(
        self, resource_path: str, claimant: Claimant | None
    ) -> uuid.UUID | None:
        if resource_path == TIME_RESOURCE:
            return None
        subject = folder_key_subject(resource_path)
        if subject is None:
            refusal = (
                "no session nonce scopes this path, and only the shared attested-time"
                " anchor is released outside a session scope"
            )
            await self.record(
                actor=DecisionActor.GUEST,
                verdict=DecisionVerdict.OUT_OF_SCOPE,
                resource_path=resource_path,
                failing_clause=refusal,
            )
            raise ShimRefusal(extra_msg=refusal)
        domain_name, folder_id = subject
        entitled = (
            None
            if claimant is None
            else await self._entitling_session(claimant.guest, domain_name, folder_id)
        )
        if entitled is None:
            refusal = (
                f"no live claim of this guest names a session that mounts folder {folder_id}"
                f" in domain {domain_name}"
            )
            await self.record(
                actor=DecisionActor.GUEST,
                verdict=DecisionVerdict.DENIED,
                resource_path=resource_path,
                failing_clause=refusal,
            )
            raise FolderKeyNotEntitled(extra_msg=refusal)
        return entitled

    async def relay_attest(
        self,
        opts: ConfidentialScalingGroupOpts,
        body: bytes,
        headers: dict[str, str],
    ) -> tuple[int, bytes, dict[str, str]]:
        try:
            evidence = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            evidence = None
        registers = presented_registers(_report_body(evidence))
        measurement = None if registers is None else json.dumps(registers)
        try:
            status, payload, resp_headers = await self._broker.relay(
                BrokerTarget.of(opts), "POST", "/kbs/v0/attest", body=body, headers=headers
            )
        except BrokerUnreachable:
            await self.record(
                actor=DecisionActor.GUEST,
                verdict=DecisionVerdict.UNREACHABLE,
                resource_path="/kbs/v0/attest",
                measurement=measurement,
            )
            raise
        guest = presented_guest(evidence)
        if status < 400 and guest is not None:
            await self._witness(
                guest,
                opts.broker_endpoint,
                await self._admitting_value(opts.broker_endpoint, registers),
            )
        await self.record(
            actor=DecisionActor.GUEST,
            verdict=DecisionVerdict.ALLOWED if status < 400 else DecisionVerdict.DENIED,
            resource_path="/kbs/v0/attest",
            measurement=measurement,
            failing_clause=None if status < 400 else payload[:512].decode("utf-8", "replace"),
        )
        return status, payload, resp_headers

    async def _admitting_value(
        self, endpoint: str, registers: dict[str, str] | None
    ) -> uuid.UUID | None:
        if registers is None:
            return None
        now = datetime.now(UTC)
        async with self._db.begin_readonly_session() as db_session:
            rows = await db_session.scalars(
                sa.select(ConfidentialReferenceValueRow).where(
                    (ConfidentialReferenceValueRow.endpoint == endpoint)
                    & (
                        (ConfidentialReferenceValueRow.state == ReferenceValueState.ACTIVE)
                        | (
                            (ConfidentialReferenceValueRow.state == ReferenceValueState.SUPERSEDED)
                            & (ConfidentialReferenceValueRow.coexistence_until > now)
                        )
                    )
                )
            )
            admitting = [row.id for row in rows.all() if admits(row.measurements, registers)]
        if len(admitting) == 1:
            return admitting[0]
        log.warning(
            "confidential: the registers a guest presented at {} name {} admissible reference"
            " values, so the session it goes on to claim carries no attribution: {}",
            endpoint,
            len(admitting),
            registers["rtmr_2"],
        )
        return None

    async def _witness(self, guest: str, endpoint: str, value_id: uuid.UUID | None) -> None:
        statement = pg_insert(ConfidentialAttestedGuestRow).values(
            guest=guest, endpoint=endpoint, reference_value_id=value_id
        )
        statement = (
            statement.on_conflict_do_nothing()
            if value_id is None
            else statement.on_conflict_do_update(
                index_elements=["guest", "endpoint"],
                set_={"reference_value_id": value_id},
            )
        )
        async with self._db.begin_session() as db_session:
            await db_session.execute(statement)

    async def _is_witnessed(self, guest: str, endpoint: str) -> bool:
        async with self._db.begin_readonly_session() as db_session:
            found = await db_session.scalar(
                sa.select(ConfidentialAttestedGuestRow.guest).where(
                    (ConfidentialAttestedGuestRow.guest == guest)
                    & (ConfidentialAttestedGuestRow.endpoint == endpoint)
                )
            )
        return found is not None

    async def relay_release(
        self,
        opts: ConfidentialScalingGroupOpts,
        resource_path: str,
        headers: dict[str, str],
    ) -> tuple[int, bytes, dict[str, str]]:
        nonce = path_nonce(resource_path)
        bearer = attested_guest(headers)
        if bearer is not None and not await self._is_witnessed(bearer.guest, opts.broker_endpoint):
            await self.record(
                actor=DecisionActor.GUEST,
                verdict=DecisionVerdict.DENIED,
                resource_path=resource_path,
                failing_clause="the bearer token names a guest that never attested through this shim",
                nonce=nonce,
            )
            raise ShimRefusal(extra_msg="this shim never witnessed the presented token attest")
        session = rcar_session(headers)
        claimant = bearer or (
            None if session is None else Claimant(session, datetime.now(UTC) + UNDATED_CLAIM_LEASE)
        )
        session_id: uuid.UUID | None = None
        consumed = False
        if nonce is None:
            session_id = await self._authorise_unscoped(resource_path, claimant)
        else:
            if claimant is None:
                await self.record(
                    actor=DecisionActor.GUEST,
                    verdict=DecisionVerdict.DENIED,
                    resource_path=resource_path,
                    failing_clause="the fetch carried no attested session identifier to claim under",
                    nonce=nonce,
                )
                raise ShimRefusal(extra_msg="an unattested fetch cannot claim a session nonce")
            try:
                session_id, consumed = await self._consume(nonce, claimant)
            except NonceQuotaExhausted:
                await self.record(
                    actor=DecisionActor.GUEST,
                    verdict=DecisionVerdict.DENIED,
                    resource_path=resource_path,
                    failing_clause="launch-nonce claim quota exhausted or nonce unknown",
                    nonce=nonce,
                )
                raise
        try:
            status, payload, resp_headers = await self._broker.relay(
                BrokerTarget.of(opts),
                "GET",
                f"/kbs/v0/resource/{resource_path}",
                body=None,
                headers=headers,
            )
        except BrokerUnreachable:
            if consumed and nonce is not None and claimant is not None:
                await self._release_claim(nonce, claimant.guest)
            await self.record(
                actor=DecisionActor.GUEST,
                verdict=DecisionVerdict.UNREACHABLE,
                resource_path=resource_path,
                session_id=session_id,
                nonce=nonce,
            )
            raise
        await self.record(
            actor=DecisionActor.GUEST,
            verdict=DecisionVerdict.ALLOWED if status < 400 else DecisionVerdict.DENIED,
            resource_path=resource_path,
            failing_clause=None if status < 400 else payload[:512].decode("utf-8", "replace"),
            session_id=session_id,
            nonce=nonce,
        )
        return status, payload, resp_headers

    async def relay_auth(
        self, opts: ConfidentialScalingGroupOpts, body: bytes, headers: dict[str, str]
    ) -> tuple[int, bytes, dict[str, str]]:
        return await self._broker.relay(
            BrokerTarget.of(opts), "POST", "/kbs/v0/auth", body=body, headers=headers
        )

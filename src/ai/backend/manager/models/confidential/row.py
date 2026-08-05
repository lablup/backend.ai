from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.models.base import GUID, Base, StrEnumType
from ai.backend.manager.models.confidential.types import (
    DecisionActor,
    DecisionVerdict,
    ReferenceValueState,
    SessionResourceKind,
)


class ConfidentialReferenceValueRow(Base):  # type: ignore[misc]
    __tablename__ = "confidential_reference_values"
    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    endpoint: Mapped[str] = mapped_column("endpoint", sa.String(length=1024), nullable=False)
    image_digest: Mapped[str] = mapped_column("image_digest", sa.String(length=256), nullable=False)
    profile_version: Mapped[str] = mapped_column(
        "profile_version", sa.String(length=64), nullable=False
    )
    measurements: Mapped[dict[str, Any]] = mapped_column(
        "measurements", pgsql.JSONB(), nullable=False
    )
    pipeline_signature: Mapped[str] = mapped_column("pipeline_signature", sa.Text, nullable=False)
    registered_by: Mapped[str] = mapped_column(
        "registered_by", sa.String(length=256), nullable=False
    )
    state: Mapped[ReferenceValueState] = mapped_column(
        "state",
        StrEnumType(ReferenceValueState),
        nullable=False,
        default=ReferenceValueState.ACTIVE,
    )
    supersedes: Mapped[uuid.UUID | None] = mapped_column("supersedes", GUID, nullable=True)
    coexistence_until: Mapped[datetime | None] = mapped_column(
        "coexistence_until", sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    __table_args__ = (sa.Index("ix_confidential_refval_endpoint_state", "endpoint", "state"),)


class ConfidentialPolicyJournalRow(Base):  # type: ignore[misc]
    __tablename__ = "confidential_policy_journal"
    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    endpoint: Mapped[str] = mapped_column(
        "endpoint", sa.String(length=1024), nullable=False, index=True
    )
    content_hash: Mapped[str] = mapped_column("content_hash", sa.String(length=96), nullable=False)
    document: Mapped[str] = mapped_column("document", sa.Text, nullable=False)
    composed_at: Mapped[datetime] = mapped_column(
        "composed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    uploaded_at: Mapped[datetime | None] = mapped_column(
        "uploaded_at", sa.DateTime(timezone=True), nullable=True
    )
    upload_failure: Mapped[str | None] = mapped_column("upload_failure", sa.Text, nullable=True)


class ConfidentialSessionResourceRow(Base):  # type: ignore[misc]
    __tablename__ = "confidential_session_resources"
    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    session_id: Mapped[uuid.UUID] = mapped_column("session_id", GUID, nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column("endpoint", sa.String(length=1024), nullable=False)
    resource_path: Mapped[str] = mapped_column(
        "resource_path", sa.String(length=512), nullable=False
    )
    kind: Mapped[SessionResourceKind] = mapped_column(
        "kind", StrEnumType(SessionResourceKind), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        "deleted_at", sa.DateTime(timezone=True), nullable=True
    )
    __table_args__ = (
        sa.UniqueConstraint("endpoint", "resource_path", name="uq_conf_resource_path"),
    )


class ConfidentialNonceRow(Base):  # type: ignore[misc]
    __tablename__ = "confidential_nonces"
    session_id: Mapped[uuid.UUID] = mapped_column("session_id", GUID, primary_key=True)
    nonce: Mapped[str] = mapped_column(
        "nonce", sa.String(length=128), nullable=False, unique=True, index=True
    )
    endpoint: Mapped[str] = mapped_column("endpoint", sa.String(length=1024), nullable=False)
    domain_name: Mapped[str] = mapped_column("domain_name", sa.String(length=64), nullable=False)
    image_digest: Mapped[str] = mapped_column("image_digest", sa.String(length=256), nullable=False)
    profile_version: Mapped[str] = mapped_column(
        "profile_version", sa.String(length=64), nullable=False
    )
    quota: Mapped[int] = mapped_column("quota", sa.Integer, nullable=False)
    claims_used: Mapped[int] = mapped_column(
        "claims_used", sa.Integer, nullable=False, server_default=sa.text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


class ConfidentialGuestClaimRow(Base):  # type: ignore[misc]
    __tablename__ = "confidential_guest_claims"
    nonce: Mapped[str] = mapped_column("nonce", sa.String(length=128), primary_key=True)
    guest: Mapped[str] = mapped_column("guest", sa.String(length=128), primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column("session_id", GUID, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


class ConfidentialAttestedGuestRow(Base):  # type: ignore[misc]
    __tablename__ = "confidential_attested_guests"
    guest: Mapped[str] = mapped_column("guest", sa.String(length=128), primary_key=True)
    endpoint: Mapped[str] = mapped_column("endpoint", sa.String(length=1024), primary_key=True)
    witnessed_at: Mapped[datetime] = mapped_column(
        "witnessed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


class ConfidentialDecisionRow(Base):  # type: ignore[misc]
    __tablename__ = "confidential_decisions"
    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    occurred_at: Mapped[datetime] = mapped_column(
        "occurred_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
        index=True,
    )
    actor: Mapped[DecisionActor] = mapped_column(
        "actor", StrEnumType(DecisionActor), nullable=False
    )
    verdict: Mapped[DecisionVerdict] = mapped_column(
        "verdict", StrEnumType(DecisionVerdict), nullable=False, index=True
    )
    resource_path: Mapped[str] = mapped_column(
        "resource_path", sa.String(length=512), nullable=False
    )
    measurement: Mapped[str | None] = mapped_column("measurement", sa.Text, nullable=True)
    failing_clause: Mapped[str | None] = mapped_column("failing_clause", sa.Text, nullable=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column("session_id", GUID, nullable=True)
    nonce: Mapped[str | None] = mapped_column("nonce", sa.String(length=128), nullable=True)


class ConfidentialMeasuredBlobRow(Base):  # type: ignore[misc]
    __tablename__ = "confidential_measured_blobs"
    endpoint: Mapped[str] = mapped_column("endpoint", sa.String(length=1024), primary_key=True)
    image_digest: Mapped[str] = mapped_column(
        "image_digest", sa.String(length=256), primary_key=True
    )
    profile_version: Mapped[str] = mapped_column(
        "profile_version", sa.String(length=64), primary_key=True
    )
    blob_digest: Mapped[str] = mapped_column("blob_digest", sa.String(length=96), nullable=False)
    blob: Mapped[bytes] = mapped_column("blob", sa.LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


class ConfidentialTcbGraceRow(Base):  # type: ignore[misc]
    __tablename__ = "confidential_tcb_grace"
    endpoint: Mapped[str] = mapped_column("endpoint", sa.String(length=1024), primary_key=True)
    platform_status: Mapped[str] = mapped_column(
        "platform_status", sa.String(length=64), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        "expires_at", sa.DateTime(timezone=True), nullable=False
    )
    disclosure: Mapped[str] = mapped_column("disclosure", sa.Text, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(
        "resolved_at", sa.DateTime(timezone=True), nullable=True
    )


class ConfidentialClientReleaseRow(Base):  # type: ignore[misc]
    __tablename__ = "confidential_client_releases"
    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    released_at: Mapped[datetime] = mapped_column(
        "released_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
        index=True,
    )
    vfolder_id: Mapped[uuid.UUID] = mapped_column("vfolder_id", GUID, nullable=False, index=True)
    domain_name: Mapped[str] = mapped_column("domain_name", sa.String(length=64), nullable=False)
    requester_id: Mapped[uuid.UUID] = mapped_column("requester_id", GUID, nullable=False)
    requester: Mapped[str] = mapped_column("requester", sa.String(length=256), nullable=False)
    session_id: Mapped[uuid.UUID | None] = mapped_column("session_id", GUID, nullable=True)
    scope: Mapped[str] = mapped_column("scope", sa.String(length=128), nullable=False)
    tier: Mapped[str] = mapped_column("tier", sa.String(length=32), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        "expires_at", sa.DateTime(timezone=True), nullable=False
    )


class ConfidentialChannelRow(Base):  # type: ignore[misc]
    __tablename__ = "confidential_channels"
    kernel_id: Mapped[uuid.UUID] = mapped_column("kernel_id", GUID, primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column("session_id", GUID, nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column("endpoint", sa.String(length=1024), nullable=False)
    resource_path: Mapped[str] = mapped_column(
        "resource_path", sa.String(length=512), nullable=False
    )
    relay_addr: Mapped[str] = mapped_column("relay_addr", sa.String(length=256), nullable=False)
    channel_port: Mapped[int] = mapped_column("channel_port", sa.Integer, nullable=False)
    fingerprint: Mapped[str] = mapped_column("fingerprint", sa.String(length=128), nullable=False)
    token: Mapped[str] = mapped_column("token", sa.String(length=256), nullable=False)
    epoch: Mapped[int] = mapped_column("epoch", sa.Integer, nullable=False, default=0)
    expires_at: Mapped[datetime] = mapped_column(
        "expires_at", sa.DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

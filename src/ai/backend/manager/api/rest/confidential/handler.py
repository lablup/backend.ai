from __future__ import annotations

import base64
import logging
import uuid
from datetime import timedelta
from http import HTTPStatus
from typing import Any, Final

import sqlalchemy as sa
from aiohttp import web
from pydantic import Field

from ai.backend.common.api_handlers import (
    APIResponse,
    BaseRequestModel,
    BaseResponseModel,
    BodyParam,
    PathParam,
)
from ai.backend.common.cc_storage import CAPABILITY_HEADER
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.confidential.plane import ConfidentialPlane, verify_capability
from ai.backend.manager.confidential.references import DEFAULT_COEXISTENCE
from ai.backend.manager.confidential.shim import (
    RELAYED_REQUEST_HEADERS,
    RELAYED_RESPONSE_HEADERS,
)
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.errors.confidential import ReleaseDenied, ShimRefusal
from ai.backend.manager.models.confidential.disclosure import confidential_capability_view
from ai.backend.manager.models.confidential.row import ConfidentialDecisionRow
from ai.backend.manager.models.confidential.types import DecisionVerdict
from ai.backend.manager.models.scaling_group.row import ScalingGroupRow
from ai.backend.manager.models.scaling_group.types import ConfidentialScalingGroupOpts
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow, VFolderStatusSet
from ai.backend.manager.models.vfolder.row import query_accessible_vfolders

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class _Payload(BaseResponseModel):
    result: dict[str, Any]


class ScalingGroupPath(BaseRequestModel):
    scaling_group: str


class ResourcePath(BaseRequestModel):
    scaling_group: str
    resource_path: str


class CapabilityRequest(BaseRequestModel):
    scaling_group: str
    confidential: ConfidentialScalingGroupOpts


class ReferenceValueRequest(BaseRequestModel):
    scaling_group: str
    attested_identity: str
    image_digest: str
    profile_version: str
    measurements: dict[str, Any]
    pipeline_signature: str
    supersedes: uuid.UUID | None = None
    coexistence_seconds: float = DEFAULT_COEXISTENCE.total_seconds()


class FolderKeyRequest(BaseRequestModel):
    vfolder_id: uuid.UUID
    session_id: uuid.UUID | None = None


class DrainRequest(BaseRequestModel):
    scaling_group: str
    reference_value_id: uuid.UUID


class EscrowRestoreRequest(BaseRequestModel):
    scaling_group: str


class BlobRequest(BaseRequestModel):
    scaling_group: str
    image_digest: str
    profile_version: str
    blob_base64: str


class GraceRequest(BaseRequestModel):
    scaling_group: str
    platform_status: str
    disclosure: str


class DecisionQuery(BaseRequestModel):
    verdict: DecisionVerdict | None = None
    session_id: uuid.UUID | None = None
    limit: int = Field(default=100, ge=1, le=1000)


class ConfidentialHandler:
    def __init__(self, *, plane: ConfidentialPlane, db: ExtendedAsyncSAEngine) -> None:
        self._plane = plane
        self._db = db

    async def relay_auth(self, path: PathParam[ScalingGroupPath], ctx: RequestCtx) -> web.Response:
        opts = await self._plane.opts_of(path.parsed.scaling_group)
        status, payload, headers = await self._plane.shim.relay_auth(
            opts, await ctx.request.read(), _forwarded(ctx.request)
        )
        return _passthrough(status, payload, headers)

    async def relay_attest(
        self, path: PathParam[ScalingGroupPath], ctx: RequestCtx
    ) -> web.Response:
        opts = await self._plane.opts_of(path.parsed.scaling_group)
        status, payload, headers = await self._plane.shim.relay_attest(
            opts, await ctx.request.read(), _forwarded(ctx.request)
        )
        return _passthrough(status, payload, headers)

    async def relay_resource(self, path: PathParam[ResourcePath], ctx: RequestCtx) -> web.Response:
        parsed = path.parsed
        opts = await self._plane.opts_of(parsed.scaling_group)
        status, payload, headers = await self._plane.shim.relay_release(
            opts, parsed.resource_path, _forwarded(ctx.request)
        )
        return _passthrough(status, payload, headers)

    async def set_capability(self, body: BodyParam[CapabilityRequest]) -> APIResponse:
        parsed = body.parsed
        await verify_capability(parsed.confidential)
        async with self._db.begin_session() as db_session:
            row = await db_session.get(ScalingGroupRow, parsed.scaling_group)
            if row is None:
                raise ShimRefusal(extra_msg=f"unknown scaling group {parsed.scaling_group}")
            row.confidential = parsed.confidential
        return APIResponse.build(
            HTTPStatus.OK, _Payload(result=confidential_capability_view(parsed.confidential))
        )

    async def register_reference_value(self, body: BodyParam[ReferenceValueRequest]) -> APIResponse:
        parsed = body.parsed
        opts = await self._plane.opts_of(parsed.scaling_group)
        row = await self._plane.references.register(
            opts,
            attested_identity=parsed.attested_identity,
            image_digest=parsed.image_digest,
            profile_version=parsed.profile_version,
            measurements=parsed.measurements,
            pipeline_signature=parsed.pipeline_signature,
            supersedes=parsed.supersedes,
            coexistence=timedelta(seconds=parsed.coexistence_seconds),
        )
        content_hash = await self._plane.policy.compose_and_upload(opts)
        return APIResponse.build(
            HTTPStatus.CREATED,
            _Payload(
                result={"reference_value_id": str(row.id), "policy_content_hash": content_hash}
            ),
        )

    async def drain_reference_value(self, body: BodyParam[DrainRequest]) -> APIResponse:
        parsed = body.parsed
        opts = await self._plane.opts_of(parsed.scaling_group)
        row = await self._plane.references.retire(parsed.reference_value_id)
        affected = await self._plane.references.sessions_on(row)
        content_hash = await self._plane.policy.compose_and_upload(opts)
        endpoints = await self._plane.confidential_endpoints()
        for session_id in affected:
            await self._plane.provisioner.teardown(endpoints, session_id)
        return APIResponse.build(
            HTTPStatus.OK,
            _Payload(
                result={
                    "policy_content_hash": content_hash,
                    "drained_sessions": [str(s) for s in affected],
                }
            ),
        )

    async def restore_folder_keys(self, body: BodyParam[EscrowRestoreRequest]) -> APIResponse:
        opts = await self._plane.opts_of(body.parsed.scaling_group)
        restored = await self._plane.custodian.restore(opts)
        return APIResponse.build(HTTPStatus.OK, _Payload(result={"restored_keys": restored}))

    async def publish_blob(self, body: BodyParam[BlobRequest]) -> APIResponse:
        parsed = body.parsed
        opts = await self._plane.opts_of(parsed.scaling_group)
        blob = base64.b64decode(parsed.blob_base64)
        digest = await self._plane.blobs.publish(
            opts.broker_endpoint, parsed.image_digest, parsed.profile_version, blob
        )
        return APIResponse.build(HTTPStatus.CREATED, _Payload(result={"blob_digest": digest}))

    async def open_grace(self, body: BodyParam[GraceRequest]) -> APIResponse:
        parsed = body.parsed
        opts = await self._plane.opts_of(parsed.scaling_group)
        row = await self._plane.policy.open_grace(opts, parsed.platform_status, parsed.disclosure)
        content_hash = await self._plane.policy.compose_and_upload(opts)
        return APIResponse.build(
            HTTPStatus.OK,
            _Payload(
                result={
                    "expires_at": row.expires_at.isoformat(),
                    "disclosure": row.disclosure,
                    "policy_content_hash": content_hash,
                }
            ),
        )

    async def list_decisions(self, body: BodyParam[DecisionQuery]) -> APIResponse:
        parsed = body.parsed
        stmt = sa.select(ConfidentialDecisionRow).order_by(
            ConfidentialDecisionRow.occurred_at.desc()
        )
        if parsed.verdict is not None:
            stmt = stmt.where(ConfidentialDecisionRow.verdict == parsed.verdict)
        if parsed.session_id is not None:
            stmt = stmt.where(ConfidentialDecisionRow.session_id == parsed.session_id)
        async with self._db.begin_readonly_session() as db_session:
            rows = (await db_session.scalars(stmt.limit(parsed.limit))).all()
        return APIResponse.build(
            HTTPStatus.OK,
            _Payload(
                result={
                    "decisions": [
                        {
                            "occurred_at": row.occurred_at.isoformat(),
                            "actor": row.actor.value,
                            "verdict": row.verdict.value,
                            "resource_path": row.resource_path,
                            "measurement": row.measurement,
                            "failing_clause": row.failing_clause,
                            "session_id": str(row.session_id) if row.session_id else None,
                            "nonce": row.nonce,
                        }
                        for row in rows
                    ]
                }
            ),
        )

    async def release_folder_key(
        self,
        body: BodyParam[FolderKeyRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        vfolder_id = body.parsed.vfolder_id
        async with self._db.begin_readonly() as conn:
            accessible = await query_accessible_vfolders(
                conn,
                ctx.user_uuid,
                user_role=ctx.user_role,
                domain_name=ctx.user_domain,
                allowed_status_set=VFolderStatusSet.READABLE,
                extra_vf_conds=(VFolderRow.id == vfolder_id),
            )
        if not accessible:
            raise ReleaseDenied(extra_msg=f"{ctx.user_email} holds no grant on folder {vfolder_id}")
        async with self._db.begin_readonly_session() as db_session:
            folder = await db_session.get(VFolderRow, vfolder_id)
        if folder is None or folder.encryption_tier is None:
            return APIResponse.build(HTTPStatus.OK, _Payload(result={"format": None}))
        release = await self._plane.client_keys.release(
            domain_name=folder.domain_name,
            vfolder_id=vfolder_id,
            tier=folder.encryption_tier,
            requester_id=ctx.user_uuid,
            requester=ctx.user_email,
            requester_domain=ctx.user_domain,
            session_id=body.parsed.session_id,
            declared_format=req.request.headers.get(CAPABILITY_HEADER),
        )
        return APIResponse.build(HTTPStatus.OK, _Payload(result=release.to_json()))


def _forwarded(request: web.Request) -> dict[str, str]:
    return {
        key: value
        for key, value in request.headers.items()
        if key.lower() in RELAYED_REQUEST_HEADERS
    }


def _passthrough(status: int, payload: bytes, headers: dict[str, str]) -> web.Response:
    return web.Response(
        status=status,
        body=payload,
        headers={
            key: value for key, value in headers.items() if key.lower() in RELAYED_RESPONSE_HEADERS
        },
    )

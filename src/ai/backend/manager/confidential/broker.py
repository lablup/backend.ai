from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Final

import aiohttp
from yarl import URL

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.confidential import (
    BrokerRejected,
    BrokerUnreachable,
    ReleaseDenied,
)
from ai.backend.manager.models.scaling_group.types import ConfidentialScalingGroupOpts

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

REQUEST_TIMEOUT: Final = aiohttp.ClientTimeout(total=10.0)
REFERENCE_VALUE_ENVELOPE_VERSION: Final = "0.1.0"


def urlsafe_nopad(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


@dataclass(frozen=True)
class BrokerTarget:
    endpoint: str
    admin_token: str

    @classmethod
    def of(cls, opts: ConfidentialScalingGroupOpts) -> BrokerTarget:
        return cls(endpoint=opts.broker_endpoint, admin_token=opts.broker_admin_token)

    @property
    def base(self) -> URL:
        return URL(self.endpoint)

    @property
    def admin_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.admin_token}"}


class BrokerClient:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def _admin(
        self,
        target: BrokerTarget,
        path: str,
        *,
        body: bytes | None = None,
        content_type: str | None = None,
        method: str = "POST",
    ) -> bytes:
        url = target.base / path.lstrip("/")
        headers = dict(target.admin_headers)
        if content_type is not None:
            headers["Content-Type"] = content_type
        try:
            async with self._session.request(
                method,
                url,
                data=body,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            ) as resp:
                payload = await resp.read()
                if resp.status >= HTTPStatus.INTERNAL_SERVER_ERROR:
                    raise BrokerUnreachable(
                        extra_msg=f"{target.endpoint} answered {resp.status} for {path}"
                    )
                if resp.status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
                    raise ReleaseDenied(
                        extra_msg=f"{target.endpoint} refused {path}: {payload[:512]!r}"
                    )
                if resp.status >= HTTPStatus.BAD_REQUEST:
                    raise BrokerRejected(
                        extra_msg=f"{target.endpoint} rejected {path}: {payload[:512]!r}"
                    )
                return payload
        except (aiohttp.ClientError, TimeoutError, OSError) as e:
            raise BrokerUnreachable(extra_msg=f"{target.endpoint} unreachable: {e}") from e

    async def put_resource(self, target: BrokerTarget, resource_path: str, payload: bytes) -> None:
        await self._admin(
            target,
            f"/kbs/v0/resource/{resource_path}",
            body=payload,
            content_type="application/octet-stream",
        )

    async def destroy_resource(
        self, target: BrokerTarget, resource_path: str, *, missing_ok: bool = False
    ) -> None:
        try:
            await self._admin(target, f"/kbs/v0/resource/{resource_path}", method="DELETE")
        except (BrokerRejected, ReleaseDenied):
            if not missing_ok:
                raise
            log.warning("confidential: {} held no {} to destroy", target.endpoint, resource_path)

    async def upload_release_policy(self, target: BrokerTarget, document: str) -> None:
        await self._admin(
            target,
            "/kbs/v0/resource-policy",
            body=json.dumps({"policy": urlsafe_nopad(document.encode("utf-8"))}).encode("utf-8"),
            content_type="application/json",
        )

    async def register_reference_value(self, target: BrokerTarget, provenance: bytes) -> None:
        await self._admin(
            target,
            "/kbs/v0/reference-value",
            body=json.dumps({
                "version": REFERENCE_VALUE_ENVELOPE_VERSION,
                "type": "sample",
                "payload": base64.b64encode(provenance).decode("ascii"),
            }).encode("utf-8"),
            content_type="application/json",
        )

    async def relay(
        self,
        target: BrokerTarget,
        method: str,
        path: str,
        *,
        body: bytes | None,
        headers: dict[str, str],
        query: dict[str, Any] | None = None,
    ) -> tuple[int, bytes, dict[str, str]]:
        url = target.base / path.lstrip("/")
        if query:
            url = url.with_query(query)
        try:
            async with self._session.request(
                method,
                url,
                data=body,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            ) as resp:
                payload = await resp.read()
                if resp.status >= HTTPStatus.INTERNAL_SERVER_ERROR:
                    raise BrokerUnreachable(
                        extra_msg=f"{target.endpoint} answered {resp.status} for {path}"
                    )
                return resp.status, payload, dict(resp.headers)
        except (aiohttp.ClientError, TimeoutError, OSError) as e:
            raise BrokerUnreachable(extra_msg=f"{target.endpoint} unreachable: {e}") from e

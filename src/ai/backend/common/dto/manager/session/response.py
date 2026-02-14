"""
Response DTOs for session endpoints.

Several handlers return raw dicts from action results — those are typed as
``dict[str, Any]`` until more precise action-result types are available.
Endpoints that return 204 NO_CONTENT or binary streams do not have a
response model.

.. todo::
   Replace ``result: dict[str, Any]`` fields with precise typed models once
   action-result schemas are formalised (see ``ActionResult`` types in the
   service layer).  Affected models: ``CreateSessionResponse``,
   ``GetCommitStatusResponse``, ``GetAbusingReportResponse``,
   ``CommitSessionResponse``, ``DestroySessionResponse``,
   ``GetSessionInfoResponse``, ``GetDirectAccessInfoResponse``,
   ``ExecuteResponse``, ``CompleteResponse``, ``ListFilesResponse``,
   ``GetContainerLogsResponse``, ``GetStatusHistoryResponse``,
   ``GetDependencyGraphResponse``.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.types import SessionId

__all__ = (
    "CommitSessionResponse",
    "CompleteResponse",
    "ConvertSessionToImageResponse",
    "CreateSessionResponse",
    "DestroySessionResponse",
    "ExecuteResponse",
    "GetAbusingReportResponse",
    "GetCommitStatusResponse",
    "GetContainerLogsResponse",
    "GetDependencyGraphResponse",
    "GetDirectAccessInfoResponse",
    "GetSessionInfoResponse",
    "GetStatusHistoryResponse",
    "ListFilesResponse",
    "MatchSessionsResponse",
    "StartServiceResponse",
    "TransitSessionStatusResponse",
)


class CreateSessionResponse(BaseResponseModel):
    """Shared response for ``create_from_template``, ``create_from_params``,
    and ``create_cluster``."""

    result: dict[str, Any] = Field(default_factory=dict)  # TODO: replace with typed model


class StartServiceResponse(BaseResponseModel):
    """POST ``/{session_name}/start-service``"""

    token: str
    wsproxy_addr: str


class GetCommitStatusResponse(BaseResponseModel):
    """GET ``/{session_name}/commit``"""

    result: dict[str, Any] = Field(default_factory=dict)  # TODO: replace with typed model


class GetAbusingReportResponse(BaseResponseModel):
    """GET ``/{session_name}/abusing-report``"""

    result: dict[str, Any] = Field(default_factory=dict)  # TODO: replace with typed model


class TransitSessionStatusResponse(BaseResponseModel):
    """POST ``/_/transit-status``"""

    session_status_map: dict[SessionId, str]


class CommitSessionResponse(BaseResponseModel):
    """POST ``/{session_name}/commit``"""

    result: dict[str, Any] = Field(default_factory=dict)  # TODO: replace with typed model


class ConvertSessionToImageResponse(BaseResponseModel):
    """POST ``/{session_name}/imagify``"""

    task_id: str


class DestroySessionResponse(BaseResponseModel):
    """DELETE ``/{session_name}``"""

    result: dict[str, Any] = Field(default_factory=dict)  # TODO: replace with typed model


class GetSessionInfoResponse(BaseResponseModel):
    """GET ``/{session_name}``"""

    result: dict[str, Any] = Field(default_factory=dict)  # TODO: replace with typed model


class GetDirectAccessInfoResponse(BaseResponseModel):
    """GET ``/{session_name}/direct-access-info``"""

    result: dict[str, Any] = Field(default_factory=dict)  # TODO: replace with typed model


class MatchSessionsResponse(BaseResponseModel):
    """GET ``/_/match``"""

    matches: list[Any] = Field(default_factory=list)


class ExecuteResponse(BaseResponseModel):
    """POST ``/{session_name}``"""

    result: dict[str, Any] = Field(default_factory=dict)  # TODO: replace with typed model


class CompleteResponse(BaseResponseModel):
    """POST ``/{session_name}/complete``"""

    result: dict[str, Any] = Field(default_factory=dict)  # TODO: replace with typed model


class ListFilesResponse(BaseResponseModel):
    """GET ``/{session_name}/files``"""

    result: dict[str, Any] = Field(default_factory=dict)  # TODO: replace with typed model


class GetContainerLogsResponse(BaseResponseModel):
    """GET ``/{session_name}/logs``"""

    result: dict[str, Any] = Field(default_factory=dict)  # TODO: replace with typed model


class GetStatusHistoryResponse(BaseResponseModel):
    """GET ``/{session_name}/status-history``"""

    result: dict[str, Any] = Field(default_factory=dict)  # TODO: replace with typed model


class GetDependencyGraphResponse(BaseResponseModel):
    """GET ``/{session_name}/dependency-graph``"""

    result: dict[str, Any] = Field(default_factory=dict)  # TODO: replace with typed model

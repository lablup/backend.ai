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

from ai.backend.common.api_handlers import BaseResponseModel, BaseRootResponseModel
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


class CreateSessionResponse(BaseRootResponseModel[dict[str, Any]]):
    """Shared response for ``create_from_template``, ``create_from_params``,
    and ``create_cluster``.

    Returns a flat JSON object (no wrapper key), so we use
    ``BaseRootResponseModel`` to preserve the original response format.
    Access the data via ``.root``.
    """


class StartServiceResponse(BaseResponseModel):
    """POST ``/{session_name}/start-service``"""

    token: str
    wsproxy_addr: str


class GetCommitStatusResponse(BaseRootResponseModel[dict[str, Any]]):
    """GET ``/{session_name}/commit``

    Returns a flat JSON object (no wrapper key), so we use
    ``BaseRootResponseModel`` to preserve the original response format.
    Access the data via ``.root``.
    """


class GetAbusingReportResponse(BaseRootResponseModel[dict[str, Any]]):
    """GET ``/{session_name}/abusing-report``

    Returns a flat JSON object (no wrapper key), so we use
    ``BaseRootResponseModel`` to preserve the original response format.
    Access the data via ``.root``.
    """


class TransitSessionStatusResponse(BaseResponseModel):
    """POST ``/_/transit-status``"""

    session_status_map: dict[SessionId, str]


class CommitSessionResponse(BaseRootResponseModel[dict[str, Any]]):
    """POST ``/{session_name}/commit``

    Returns a flat JSON object (no wrapper key), so we use
    ``BaseRootResponseModel`` to preserve the original response format.
    Access the data via ``.root``.
    """


class ConvertSessionToImageResponse(BaseResponseModel):
    """POST ``/{session_name}/imagify``"""

    task_id: str


class DestroySessionResponse(BaseRootResponseModel[dict[str, Any]]):
    """DELETE ``/{session_name}``

    Returns a flat JSON object (no wrapper key), so we use
    ``BaseRootResponseModel`` to preserve the original response format.
    Access the data via ``.root``.
    """


class GetSessionInfoResponse(BaseRootResponseModel[dict[str, Any]]):
    """GET ``/{session_name}``

    The API handler returns ``session_info.asdict()`` as a flat JSON object
    (no wrapper key), so we use ``BaseRootResponseModel`` to capture the entire
    payload.  Access the data via ``.root``.
    """


class GetDirectAccessInfoResponse(BaseRootResponseModel[dict[str, Any]]):
    """GET ``/{session_name}/direct-access-info``

    Returns a flat JSON object (no wrapper key), so we use
    ``BaseRootResponseModel`` to preserve the original response format.
    Access the data via ``.root``.
    """


class MatchSessionsResponse(BaseResponseModel):
    """GET ``/_/match``"""

    matches: list[Any] = Field(default_factory=list)


class ExecuteResponse(BaseRootResponseModel[dict[str, Any]]):
    """POST ``/{session_name}``

    Returns a flat JSON object (no wrapper key), so we use
    ``BaseRootResponseModel`` to preserve the original response format.
    Access the data via ``.root``.
    """


class CompleteResponse(BaseRootResponseModel[dict[str, Any]]):
    """POST ``/{session_name}/complete``

    Returns a flat JSON object (no wrapper key), so we use
    ``BaseRootResponseModel`` to preserve the original response format.
    Access the data via ``.root``.
    """


class ListFilesResponse(BaseRootResponseModel[dict[str, Any]]):
    """GET ``/{session_name}/files``

    Returns a flat JSON object (no wrapper key), so we use
    ``BaseRootResponseModel`` to preserve the original response format.
    Access the data via ``.root``.
    """


class GetContainerLogsResponse(BaseRootResponseModel[dict[str, Any]]):
    """GET ``/{session_name}/logs``

    Returns a flat JSON object (no wrapper key), so we use
    ``BaseRootResponseModel`` to preserve the original response format.
    Access the data via ``.root``.
    """


class GetStatusHistoryResponse(BaseRootResponseModel[dict[str, Any]]):
    """GET ``/{session_name}/status-history``

    Returns a flat JSON object (no wrapper key), so we use
    ``BaseRootResponseModel`` to preserve the original response format.
    Access the data via ``.root``.
    """


class GetDependencyGraphResponse(BaseRootResponseModel[dict[str, Any]]):
    """GET ``/{session_name}/dependency-graph``

    Returns a flat JSON object (no wrapper key), so we use
    ``BaseRootResponseModel`` to preserve the original response format.
    Access the data via ``.root``.
    """

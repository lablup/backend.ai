"""
Common DTOs for template management system used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import (
    CreateClusterTemplateRequest,
    CreateSessionTemplateRequest,
    DeleteClusterTemplateRequest,
    DeleteSessionTemplateRequest,
    GetClusterTemplateRequest,
    GetSessionTemplateRequest,
    ListClusterTemplatesRequest,
    ListSessionTemplatesRequest,
    TemplatePathParam,
    UpdateClusterTemplateRequest,
    UpdateSessionTemplateRequest,
)
from .response import (
    ClusterTemplateListItemDTO,
    CreateClusterTemplateResponse,
    CreateSessionTemplateItemDTO,
    CreateSessionTemplateResponse,
    DeleteClusterTemplateResponse,
    DeleteSessionTemplateResponse,
    GetClusterTemplateResponse,
    GetSessionTemplateResponse,
    ListClusterTemplatesResponse,
    ListSessionTemplatesResponse,
    SessionTemplateItemDTO,
    SessionTemplateListItemDTO,
    UpdateClusterTemplateResponse,
    UpdateSessionTemplateResponse,
)

__all__ = (
    # Request DTOs - Path params
    "TemplatePathParam",
    # Request DTOs - Session template
    "CreateSessionTemplateRequest",
    "ListSessionTemplatesRequest",
    "GetSessionTemplateRequest",
    "UpdateSessionTemplateRequest",
    "DeleteSessionTemplateRequest",
    # Request DTOs - Cluster template
    "CreateClusterTemplateRequest",
    "ListClusterTemplatesRequest",
    "GetClusterTemplateRequest",
    "UpdateClusterTemplateRequest",
    "DeleteClusterTemplateRequest",
    # Response DTOs - Shared
    "SessionTemplateItemDTO",
    "SessionTemplateListItemDTO",
    "ClusterTemplateListItemDTO",
    "CreateSessionTemplateItemDTO",
    # Response DTOs - Session template
    "CreateSessionTemplateResponse",
    "ListSessionTemplatesResponse",
    "GetSessionTemplateResponse",
    "UpdateSessionTemplateResponse",
    "DeleteSessionTemplateResponse",
    # Response DTOs - Cluster template
    "CreateClusterTemplateResponse",
    "ListClusterTemplatesResponse",
    "GetClusterTemplateResponse",
    "UpdateClusterTemplateResponse",
    "DeleteClusterTemplateResponse",
)

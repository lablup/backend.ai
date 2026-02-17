from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class GetQuotaScopePathParam(BaseRequestModel):
    storage_host_name: str = Field(description="The storage host name")
    quota_scope_id: str = Field(
        description="The quota scope ID (e.g. 'user:<uuid>' or 'project:<uuid>')"
    )

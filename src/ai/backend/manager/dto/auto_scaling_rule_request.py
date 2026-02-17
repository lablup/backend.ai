import uuid

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class GetAutoScalingRulePathParam(BaseRequestModel):
    rule_id: uuid.UUID = Field(description="The auto-scaling rule ID to retrieve")


class UpdateAutoScalingRulePathParam(BaseRequestModel):
    rule_id: uuid.UUID = Field(description="The auto-scaling rule ID to update")

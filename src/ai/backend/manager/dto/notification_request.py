import uuid

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.notification import NotificationRuleType


class UpdateNotificationChannelPathParam(BaseRequestModel):
    channel_id: uuid.UUID = Field(description="The notification channel ID to update")


class GetNotificationChannelPathParam(BaseRequestModel):
    channel_id: uuid.UUID = Field(description="The notification channel ID to retrieve")


class DeleteNotificationChannelPathParam(BaseRequestModel):
    channel_id: uuid.UUID = Field(description="The notification channel ID to delete")


class UpdateNotificationRulePathParam(BaseRequestModel):
    rule_id: uuid.UUID = Field(description="The notification rule ID to update")


class GetNotificationRulePathParam(BaseRequestModel):
    rule_id: uuid.UUID = Field(description="The notification rule ID to retrieve")


class DeleteNotificationRulePathParam(BaseRequestModel):
    rule_id: uuid.UUID = Field(description="The notification rule ID to delete")


class ValidateNotificationChannelPathParam(BaseRequestModel):
    channel_id: uuid.UUID = Field(description="The notification channel ID to validate")


class ValidateNotificationRulePathParam(BaseRequestModel):
    rule_id: uuid.UUID = Field(description="The notification rule ID to validate")


class RuleTypePathParam(BaseRequestModel):
    rule_type: NotificationRuleType = Field(
        description="The notification rule type to get schema for"
    )

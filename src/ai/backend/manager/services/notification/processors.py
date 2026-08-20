from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.actions.v2.single_entity.processor import (
    SingleEntityActionProcessor,
)
from ai.backend.manager.data.notification.types import (
    NotificationChannelData,
    NotificationRuleData,
)
from ai.backend.manager.services.notification.actions.create_channel import CreateChannelAction
from ai.backend.manager.services.notification.actions.create_rule import CreateRuleAction
from ai.backend.manager.services.notification.actions.get_channel import GetChannelAction
from ai.backend.manager.services.notification.actions.get_rule import GetRuleAction
from ai.backend.manager.services.notification.actions.list_channels import SearchChannelsAction
from ai.backend.manager.services.notification.actions.list_rules import SearchRulesAction
from ai.backend.manager.services.notification.actions.process_notification import (
    ProcessNotificationAction,
    ProcessNotificationActionResult,
)
from ai.backend.manager.services.notification.actions.purge_channel import PurgeChannelAction
from ai.backend.manager.services.notification.actions.purge_rule import PurgeRuleAction
from ai.backend.manager.services.notification.actions.update_channel import UpdateChannelAction
from ai.backend.manager.services.notification.actions.update_rule import UpdateRuleAction
from ai.backend.manager.services.notification.actions.validate_channel import (
    ValidateChannelAction,
    ValidateChannelActionResult,
)
from ai.backend.manager.services.notification.actions.validate_rule import (
    ValidateRuleAction,
    ValidateRuleActionResult,
)
from ai.backend.manager.services.notification.service import NotificationService


class NotificationProcessors:
    """Both catalogs run against ops; only dispatch and the two validations keep a service."""

    create_channel: GlobalActionProcessor[
        CreateChannelAction, CreatedEntityOpsResult[NotificationChannelData]
    ]
    update_channel: SingleEntityActionProcessor[
        UpdateChannelAction, EntityOpsResult[NotificationChannelData]
    ]
    purge_channel: SingleEntityActionProcessor[
        PurgeChannelAction, EntityOpsResult[NotificationChannelData]
    ]
    get_channel: SingleEntityActionProcessor[
        GetChannelAction, EntityOpsResult[NotificationChannelData]
    ]
    search_channels: GlobalActionProcessor[
        SearchChannelsAction, BatchOpsResult[NotificationChannelData]
    ]
    create_rule: GlobalActionProcessor[
        CreateRuleAction, CreatedEntityOpsResult[NotificationRuleData]
    ]
    update_rule: SingleEntityActionProcessor[
        UpdateRuleAction, EntityOpsResult[NotificationRuleData]
    ]
    purge_rule: SingleEntityActionProcessor[PurgeRuleAction, EntityOpsResult[NotificationRuleData]]
    get_rule: SingleEntityActionProcessor[GetRuleAction, EntityOpsResult[NotificationRuleData]]
    search_rules: GlobalActionProcessor[SearchRulesAction, BatchOpsResult[NotificationRuleData]]
    validate_channel: SingleEntityActionProcessor[
        ValidateChannelAction, ValidateChannelActionResult
    ]
    validate_rule: SingleEntityActionProcessor[ValidateRuleAction, ValidateRuleActionResult]
    process_notification: GlobalActionProcessor[
        ProcessNotificationAction, ProcessNotificationActionResult
    ]

    def __init__(
        self,
        channel_group: ProcessorGroup[NotificationChannelData],
        rule_group: ProcessorGroup[NotificationRuleData],
        service: NotificationService,
    ) -> None:
        self.create_channel = channel_group.global_create_ops(CreateChannelAction)
        self.update_channel = channel_group.single_update_ops(UpdateChannelAction)
        self.purge_channel = channel_group.entity_purge_ops(PurgeChannelAction)
        self.get_channel = channel_group.single_get_ops(GetChannelAction)
        self.search_channels = channel_group.global_search_ops(SearchChannelsAction)
        self.create_rule = rule_group.global_create_ops(CreateRuleAction)
        self.update_rule = rule_group.single_update_ops(UpdateRuleAction)
        self.purge_rule = rule_group.entity_purge_ops(PurgeRuleAction)
        self.get_rule = rule_group.single_get_ops(GetRuleAction)
        self.search_rules = rule_group.global_search_ops(SearchRulesAction)
        self.validate_channel = channel_group.single_entity(
            ValidateChannelAction, service.validate_channel
        )
        self.validate_rule = rule_group.single_entity(ValidateRuleAction, service.validate_rule)
        self.process_notification = rule_group.global_scope(
            ProcessNotificationAction, service.process_notification
        )

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec

from .actions import (
    CreateChannelAction,
    CreateChannelActionResult,
    CreateRuleAction,
    CreateRuleActionResult,
    DeleteChannelAction,
    DeleteChannelActionResult,
    DeleteRuleAction,
    DeleteRuleActionResult,
    GetChannelAction,
    GetChannelActionResult,
    GetRuleAction,
    GetRuleActionResult,
    ProcessNotificationAction,
    ProcessNotificationActionResult,
    SearchChannelsAction,
    SearchChannelsActionResult,
    SearchRulesAction,
    SearchRulesActionResult,
    UpdateChannelAction,
    UpdateChannelActionResult,
    UpdateRuleAction,
    UpdateRuleActionResult,
    ValidateChannelAction,
    ValidateChannelActionResult,
    ValidateRuleAction,
    ValidateRuleActionResult,
)
from .service import NotificationService


class NotificationProcessors(AbstractProcessorPackage):
    """Processor package for notification operations."""

    create_channel: ActionProcessor[CreateChannelAction, CreateChannelActionResult]
    search_channels: ActionProcessor[SearchChannelsAction, SearchChannelsActionResult]
    get_channel: ActionProcessor[GetChannelAction, GetChannelActionResult]
    update_channel: ActionProcessor[UpdateChannelAction, UpdateChannelActionResult]
    delete_channel: ActionProcessor[DeleteChannelAction, DeleteChannelActionResult]
    validate_channel: ActionProcessor[ValidateChannelAction, ValidateChannelActionResult]

    create_rule: ActionProcessor[CreateRuleAction, CreateRuleActionResult]
    search_rules: ActionProcessor[SearchRulesAction, SearchRulesActionResult]
    get_rule: ActionProcessor[GetRuleAction, GetRuleActionResult]
    update_rule: ActionProcessor[UpdateRuleAction, UpdateRuleActionResult]
    delete_rule: ActionProcessor[DeleteRuleAction, DeleteRuleActionResult]
    validate_rule: ActionProcessor[ValidateRuleAction, ValidateRuleActionResult]

    process_notification: ActionProcessor[
        ProcessNotificationAction, ProcessNotificationActionResult
    ]

    def __init__(self, service: NotificationService, action_monitors: list[ActionMonitor]) -> None:
        self.create_channel = ActionProcessor(service.create_channel, action_monitors)
        self.search_channels = ActionProcessor(service.search_channels, action_monitors)
        self.get_channel = ActionProcessor(service.get_channel, action_monitors)
        self.update_channel = ActionProcessor(service.update_channel, action_monitors)
        self.delete_channel = ActionProcessor(service.delete_channel, action_monitors)
        self.validate_channel = ActionProcessor(service.validate_channel, action_monitors)

        self.create_rule = ActionProcessor(service.create_rule, action_monitors)
        self.search_rules = ActionProcessor(service.search_rules, action_monitors)
        self.get_rule = ActionProcessor(service.get_rule, action_monitors)
        self.update_rule = ActionProcessor(service.update_rule, action_monitors)
        self.delete_rule = ActionProcessor(service.delete_rule, action_monitors)
        self.validate_rule = ActionProcessor(service.validate_rule, action_monitors)

        self.process_notification = ActionProcessor(service.process_notification, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateChannelAction.spec(),
            SearchChannelsAction.spec(),
            GetChannelAction.spec(),
            UpdateChannelAction.spec(),
            DeleteChannelAction.spec(),
            ValidateChannelAction.spec(),
            CreateRuleAction.spec(),
            SearchRulesAction.spec(),
            GetRuleAction.spec(),
            UpdateRuleAction.spec(),
            DeleteRuleAction.spec(),
            ValidateRuleAction.spec(),
            ProcessNotificationAction.spec(),
        ]

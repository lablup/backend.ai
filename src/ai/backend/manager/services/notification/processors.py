from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators

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

    # Scope actions (operate on GLOBAL scope)
    create_channel: ScopeActionProcessor[CreateChannelAction, CreateChannelActionResult]
    search_channels: ScopeActionProcessor[SearchChannelsAction, SearchChannelsActionResult]

    # Single-entity actions (operate on specific notification channels)
    get_channel: SingleEntityActionProcessor[GetChannelAction, GetChannelActionResult]
    update_channel: SingleEntityActionProcessor[UpdateChannelAction, UpdateChannelActionResult]
    delete_channel: SingleEntityActionProcessor[DeleteChannelAction, DeleteChannelActionResult]
    validate_channel: SingleEntityActionProcessor[
        ValidateChannelAction, ValidateChannelActionResult
    ]

    # Internal/system actions (no RBAC)
    create_rule: ActionProcessor[CreateRuleAction, CreateRuleActionResult]
    search_rules: ActionProcessor[SearchRulesAction, SearchRulesActionResult]
    get_rule: ActionProcessor[GetRuleAction, GetRuleActionResult]
    update_rule: ActionProcessor[UpdateRuleAction, UpdateRuleActionResult]
    delete_rule: ActionProcessor[DeleteRuleAction, DeleteRuleActionResult]
    validate_rule: ActionProcessor[ValidateRuleAction, ValidateRuleActionResult]

    process_notification: ActionProcessor[
        ProcessNotificationAction, ProcessNotificationActionResult
    ]

    def __init__(
        self,
        service: NotificationService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        # Scope actions with RBAC validators
        self.create_channel = ScopeActionProcessor(
            service.create_channel, action_monitors, validators=[validators.rbac.scope]
        )
        self.search_channels = ScopeActionProcessor(
            service.search_channels, action_monitors, validators=[validators.rbac.scope]
        )

        # Single-entity actions with RBAC validators
        self.get_channel = SingleEntityActionProcessor(
            service.get_channel, action_monitors, validators=[validators.rbac.single_entity]
        )
        self.update_channel = SingleEntityActionProcessor(
            service.update_channel, action_monitors, validators=[validators.rbac.single_entity]
        )
        self.delete_channel = SingleEntityActionProcessor(
            service.delete_channel, action_monitors, validators=[validators.rbac.single_entity]
        )
        self.validate_channel = SingleEntityActionProcessor(
            service.validate_channel, action_monitors, validators=[validators.rbac.single_entity]
        )

        # Internal/system actions (no RBAC validators)
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

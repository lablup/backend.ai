"""Notification handler class using constructor dependency injection."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.data.notification import NotifiableMessage
from ai.backend.common.data.notification.types import NotificationRuleType
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.dto.manager.notification import (
    CreateNotificationChannelRequest,
    CreateNotificationChannelResponse,
    CreateNotificationRuleRequest,
    CreateNotificationRuleResponse,
    DeleteNotificationChannelResponse,
    DeleteNotificationRuleResponse,
    GetNotificationChannelResponse,
    GetNotificationRuleResponse,
    ListNotificationChannelsResponse,
    ListNotificationRulesResponse,
    ListNotificationRuleTypesResponse,
    NotificationRuleTypeSchemaResponse,
    PaginationInfo,
    SearchNotificationChannelsRequest,
    SearchNotificationRulesRequest,
    UpdateNotificationChannelRequest,
    UpdateNotificationChannelResponse,
    UpdateNotificationRuleRequest,
    UpdateNotificationRuleResponse,
    ValidateNotificationChannelRequest,
    ValidateNotificationChannelResponse,
    ValidateNotificationRuleRequest,
    ValidateNotificationRuleResponse,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.dto.notification_request import (
    DeleteNotificationChannelPathParam,
    DeleteNotificationRulePathParam,
    GetNotificationChannelPathParam,
    GetNotificationRulePathParam,
    RuleTypePathParam,
    UpdateNotificationChannelPathParam,
    UpdateNotificationRulePathParam,
    ValidateNotificationChannelPathParam,
    ValidateNotificationRulePathParam,
)
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.notification.creators import (
    NotificationChannelCreatorSpec,
    NotificationRuleCreatorSpec,
)
from ai.backend.manager.services.notification.actions import (
    CreateChannelAction,
    CreateRuleAction,
    DeleteChannelAction,
    DeleteRuleAction,
    GetChannelAction,
    GetRuleAction,
    SearchChannelsAction,
    SearchRulesAction,
    UpdateChannelAction,
    UpdateRuleAction,
    ValidateChannelAction,
    ValidateRuleAction,
)
from ai.backend.manager.services.notification.processors import NotificationProcessors

from .adapter import NotificationChannelAdapter, NotificationRuleAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class NotificationHandler:
    """Notification API handler with constructor-injected dependencies."""

    def __init__(self, *, notification: NotificationProcessors) -> None:
        self._notification = notification
        self._channel_adapter = NotificationChannelAdapter()
        self._rule_adapter = NotificationRuleAdapter()

    # -- Channel endpoints --

    async def create_channel(
        self,
        body: BodyParam[CreateNotificationChannelRequest],
        ctx: UserContext,
    ) -> APIResponse:
        log.info("CREATE_CHANNEL (ak:{})", ctx.access_key)
        validated_spec = body.parsed.spec
        creator = RBACEntityCreator(
            spec=NotificationChannelCreatorSpec(
                name=body.parsed.name,
                description=body.parsed.description,
                channel_type=body.parsed.channel_type,
                spec=validated_spec,
                enabled=body.parsed.enabled,
                created_by=ctx.user_uuid,
            ),
            element_type=RBACElementType.NOTIFICATION_CHANNEL,
            scope_ref=RBACElementRef(RBACElementType.USER, str(ctx.user_uuid)),
        )
        action_result = await self._notification.create_channel.wait_for_complete(
            CreateChannelAction(creator=creator)
        )
        resp = CreateNotificationChannelResponse(
            channel=self._channel_adapter.convert_to_dto(action_result.channel_data)
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    async def search_channels(
        self,
        body: BodyParam[SearchNotificationChannelsRequest],
    ) -> APIResponse:
        querier = self._channel_adapter.build_querier(body.parsed)
        action_result = await self._notification.search_channels.wait_for_complete(
            SearchChannelsAction(querier=querier)
        )
        resp = ListNotificationChannelsResponse(
            channels=[self._channel_adapter.convert_to_dto(ch) for ch in action_result.channels],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset or 0,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def get_channel(
        self,
        path: PathParam[GetNotificationChannelPathParam],
    ) -> APIResponse:
        action_result = await self._notification.get_channel.wait_for_complete(
            GetChannelAction(channel_id=path.parsed.channel_id)
        )
        resp = GetNotificationChannelResponse(
            channel=self._channel_adapter.convert_to_dto(action_result.channel_data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def update_channel(
        self,
        path: PathParam[UpdateNotificationChannelPathParam],
        body: BodyParam[UpdateNotificationChannelRequest],
    ) -> APIResponse:
        channel_id = path.parsed.channel_id
        action_result = await self._notification.update_channel.wait_for_complete(
            UpdateChannelAction(
                updater=self._channel_adapter.build_updater(body.parsed, channel_id)
            )
        )
        resp = UpdateNotificationChannelResponse(
            channel=self._channel_adapter.convert_to_dto(action_result.channel_data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def delete_channel(
        self,
        path: PathParam[DeleteNotificationChannelPathParam],
    ) -> APIResponse:
        action_result = await self._notification.delete_channel.wait_for_complete(
            DeleteChannelAction(channel_id=path.parsed.channel_id)
        )
        resp = DeleteNotificationChannelResponse(deleted=action_result.deleted)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def validate_channel(
        self,
        path: PathParam[ValidateNotificationChannelPathParam],
        body: BodyParam[ValidateNotificationChannelRequest],
    ) -> APIResponse:
        await self._notification.validate_channel.wait_for_complete(
            ValidateChannelAction(
                channel_id=path.parsed.channel_id,
                test_message=body.parsed.test_message,
            )
        )
        resp = ValidateNotificationChannelResponse(
            channel_id=path.parsed.channel_id,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # -- Rule type endpoints --

    async def list_rule_types(self) -> APIResponse:
        resp = ListNotificationRuleTypesResponse(rule_types=list(NotificationRuleType))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def get_rule_type_schema(
        self,
        path: PathParam[RuleTypePathParam],
    ) -> APIResponse:
        schema = NotifiableMessage.get_message_schema(path.parsed.rule_type)
        resp = NotificationRuleTypeSchemaResponse(
            rule_type=path.parsed.rule_type,
            json_schema=schema,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # -- Rule endpoints --

    async def create_rule(
        self,
        body: BodyParam[CreateNotificationRuleRequest],
        ctx: UserContext,
    ) -> APIResponse:
        log.info("CREATE_RULE (ak:{})", ctx.access_key)
        creator = RBACEntityCreator(
            spec=NotificationRuleCreatorSpec(
                name=body.parsed.name,
                description=body.parsed.description,
                rule_type=body.parsed.rule_type,
                channel_id=body.parsed.channel_id,
                message_template=body.parsed.message_template,
                enabled=body.parsed.enabled,
                created_by=ctx.user_uuid,
            ),
            element_type=RBACElementType.NOTIFICATION_RULE,
            scope_ref=RBACElementRef(
                RBACElementType.NOTIFICATION_CHANNEL, str(body.parsed.channel_id)
            ),
        )
        action_result = await self._notification.create_rule.wait_for_complete(
            CreateRuleAction(creator=creator)
        )
        resp = CreateNotificationRuleResponse(
            rule=self._rule_adapter.convert_to_dto(action_result.rule_data)
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    async def search_rules(
        self,
        body: BodyParam[SearchNotificationRulesRequest],
    ) -> APIResponse:
        querier = self._rule_adapter.build_querier(body.parsed)
        action_result = await self._notification.search_rules.wait_for_complete(
            SearchRulesAction(querier=querier)
        )
        resp = ListNotificationRulesResponse(
            rules=[self._rule_adapter.convert_to_dto(rule) for rule in action_result.rules],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset or 0,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def get_rule(
        self,
        path: PathParam[GetNotificationRulePathParam],
    ) -> APIResponse:
        action_result = await self._notification.get_rule.wait_for_complete(
            GetRuleAction(rule_id=path.parsed.rule_id)
        )
        resp = GetNotificationRuleResponse(
            rule=self._rule_adapter.convert_to_dto(action_result.rule_data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def update_rule(
        self,
        path: PathParam[UpdateNotificationRulePathParam],
        body: BodyParam[UpdateNotificationRuleRequest],
    ) -> APIResponse:
        rule_id = path.parsed.rule_id
        action_result = await self._notification.update_rule.wait_for_complete(
            UpdateRuleAction(updater=self._rule_adapter.build_updater(body.parsed, rule_id))
        )
        resp = UpdateNotificationRuleResponse(
            rule=self._rule_adapter.convert_to_dto(action_result.rule_data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def delete_rule(
        self,
        path: PathParam[DeleteNotificationRulePathParam],
    ) -> APIResponse:
        action_result = await self._notification.delete_rule.wait_for_complete(
            DeleteRuleAction(rule_id=path.parsed.rule_id)
        )
        resp = DeleteNotificationRuleResponse(deleted=action_result.deleted)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def validate_rule(
        self,
        path: PathParam[ValidateNotificationRulePathParam],
        body: BodyParam[ValidateNotificationRuleRequest],
    ) -> APIResponse:
        action_result = await self._notification.validate_rule.wait_for_complete(
            ValidateRuleAction(
                rule_id=path.parsed.rule_id,
                notification_data=body.parsed.notification_data,
            )
        )
        resp = ValidateNotificationRuleResponse(
            message=action_result.message,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

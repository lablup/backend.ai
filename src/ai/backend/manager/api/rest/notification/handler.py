"""Notification handler class using constructor dependency injection."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.data.entity.notification import (
    NotificationChannelID,
    NotificationRuleID,
)
from ai.backend.common.data.notification import NotifiableMessage
from ai.backend.common.data.notification.types import NotificationRuleType
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
from ai.backend.manager.models.notification.creators import (
    NotificationChannelCreator,
    NotificationRuleCreator,
)
from ai.backend.manager.services.notification.actions import (
    CreateChannelAction,
    CreateRuleAction,
    GetChannelAction,
    GetRuleAction,
    PurgeChannelAction,
    PurgeRuleAction,
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
        creator = NotificationChannelCreator(
            name=body.parsed.name,
            description=body.parsed.description,
            channel_type=body.parsed.channel_type,
            spec=validated_spec,
            enabled=body.parsed.enabled,
            created_by=ctx.user_uuid,
        )
        action_result = await self._notification.create_channel.run(
            CreateChannelAction(creator=creator)
        )
        resp = CreateNotificationChannelResponse(
            channel=self._channel_adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    async def search_channels(
        self,
        body: BodyParam[SearchNotificationChannelsRequest],
    ) -> APIResponse:
        searcher = self._channel_adapter.build_searcher(body.parsed)
        action_result = await self._notification.search_channels.run(
            SearchChannelsAction(searcher=searcher)
        )
        resp = ListNotificationChannelsResponse(
            channels=[self._channel_adapter.convert_to_dto(ch) for ch in action_result.items],
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
        action_result = await self._notification.get_channel.run(
            GetChannelAction(channel_id=NotificationChannelID(path.parsed.channel_id))
        )
        resp = GetNotificationChannelResponse(
            channel=self._channel_adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def update_channel(
        self,
        path: PathParam[UpdateNotificationChannelPathParam],
        body: BodyParam[UpdateNotificationChannelRequest],
    ) -> APIResponse:
        channel_id = path.parsed.channel_id
        action_result = await self._notification.update_channel.run(
            UpdateChannelAction(
                updater=self._channel_adapter.build_updater(
                    body.parsed, NotificationChannelID(channel_id)
                )
            )
        )
        resp = UpdateNotificationChannelResponse(
            channel=self._channel_adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def delete_channel(
        self,
        path: PathParam[DeleteNotificationChannelPathParam],
    ) -> APIResponse:
        await self._notification.purge_channel.run(
            PurgeChannelAction(channel_id=NotificationChannelID(path.parsed.channel_id))
        )
        resp = DeleteNotificationChannelResponse(deleted=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def validate_channel(
        self,
        path: PathParam[ValidateNotificationChannelPathParam],
        body: BodyParam[ValidateNotificationChannelRequest],
    ) -> APIResponse:
        await self._notification.validate_channel.run(
            ValidateChannelAction(
                channel_id=NotificationChannelID(path.parsed.channel_id),
                test_message=body.parsed.test_message,
            )
        )
        resp = ValidateNotificationChannelResponse(
            channel_id=NotificationChannelID(path.parsed.channel_id),
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
        creator = NotificationRuleCreator(
            name=body.parsed.name,
            description=body.parsed.description,
            rule_type=body.parsed.rule_type,
            channel_id=NotificationChannelID(body.parsed.channel_id),
            message_template=body.parsed.message_template,
            enabled=body.parsed.enabled,
            created_by=ctx.user_uuid,
        )
        action_result = await self._notification.create_rule.run(CreateRuleAction(creator=creator))
        resp = CreateNotificationRuleResponse(
            rule=self._rule_adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    async def search_rules(
        self,
        body: BodyParam[SearchNotificationRulesRequest],
    ) -> APIResponse:
        searcher = self._rule_adapter.build_searcher(body.parsed)
        action_result = await self._notification.search_rules.run(
            SearchRulesAction(searcher=searcher)
        )
        resp = ListNotificationRulesResponse(
            rules=[self._rule_adapter.convert_to_dto(rule) for rule in action_result.items],
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
        action_result = await self._notification.get_rule.run(
            GetRuleAction(rule_id=NotificationRuleID(path.parsed.rule_id))
        )
        resp = GetNotificationRuleResponse(
            rule=self._rule_adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def update_rule(
        self,
        path: PathParam[UpdateNotificationRulePathParam],
        body: BodyParam[UpdateNotificationRuleRequest],
    ) -> APIResponse:
        rule_id = path.parsed.rule_id
        action_result = await self._notification.update_rule.run(
            UpdateRuleAction(
                updater=self._rule_adapter.build_updater(body.parsed, NotificationRuleID(rule_id))
            )
        )
        resp = UpdateNotificationRuleResponse(
            rule=self._rule_adapter.convert_to_dto(action_result.data)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def delete_rule(
        self,
        path: PathParam[DeleteNotificationRulePathParam],
    ) -> APIResponse:
        await self._notification.purge_rule.run(
            PurgeRuleAction(rule_id=NotificationRuleID(path.parsed.rule_id))
        )
        resp = DeleteNotificationRuleResponse(deleted=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def validate_rule(
        self,
        path: PathParam[ValidateNotificationRulePathParam],
        body: BodyParam[ValidateNotificationRuleRequest],
    ) -> APIResponse:
        action_result = await self._notification.validate_rule.run(
            ValidateRuleAction(
                rule_id=NotificationRuleID(path.parsed.rule_id),
                notification_data=body.parsed.notification_data,
            )
        )
        resp = ValidateNotificationRuleResponse(
            message=action_result.message,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

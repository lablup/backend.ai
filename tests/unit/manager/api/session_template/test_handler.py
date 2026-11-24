from __future__ import annotations

import json
import uuid
from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web
from aiohttp.web_urldispatcher import UrlMappingMatchInfo

from ai.backend.common.api_handlers import BodyParam, PathParam
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.dto.manager.template.request import (
    CreateSessionTemplateRequest,
    TemplatePathParam,
    UpdateSessionTemplateRequest,
)
from ai.backend.manager.actions.v2.ops.result import LookupOpsResult
from ai.backend.manager.api.rest.session_template.handler import SessionTemplateHandler
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.user.row import UserRole
from ai.backend.manager.services.template.actions.create_task_template import (
    CreatedTaskTemplateItem,
    CreateTaskTemplateActionResult,
)
from ai.backend.manager.services.template.actions.update_task_template import (
    UpdateTaskTemplateActionResult,
)

TEMPLATE = {"kind": "task_template", "spec": {"kernel": {"image": "python:3.11"}}}

INVALID_PAYLOADS = [
    pytest.param(json.dumps({"template": TEMPLATE}), id="an-object"),
    pytest.param("just-a-string", id="a-string"),
    pytest.param(json.dumps([{"name": "no-template"}]), id="an-item-without-template"),
    pytest.param(json.dumps(["not-an-object"]), id="an-item-not-an-object"),
]


@pytest.fixture
def mock_processors() -> MagicMock:
    mock_processors = MagicMock()
    mock_processors.project.lookup.run = AsyncMock(
        return_value=LookupOpsResult(resolved_entity_id=ProjectID(uuid.uuid4()))
    )
    return mock_processors


@pytest.fixture
def handler(mock_processors: MagicMock) -> SessionTemplateHandler:
    return SessionTemplateHandler(
        template=mock_processors.template, project=mock_processors.project
    )


@pytest.fixture
def user_ctx() -> UserContext:
    return UserContext(
        user_uuid=uuid.uuid4(),
        user_email="user@example.com",
        user_domain="default",
        user_role=UserRole.USER,
        access_key="AKTEST",
        is_admin=False,
        is_superadmin=False,
    )


@pytest.fixture
def req_ctx() -> RequestCtx:
    request = MagicMock(spec=web.Request)
    storage: dict[str, Any] = {"user": {"role": UserRole.USER}}
    request.__getitem__ = lambda _, key: storage[key]
    return RequestCtx(request=request)


def _create_body(payload: str) -> BodyParam[CreateSessionTemplateRequest]:
    body: BodyParam[CreateSessionTemplateRequest] = BodyParam(CreateSessionTemplateRequest)
    return body.from_body({"payload": payload})


def _update_body(payload: str) -> BodyParam[UpdateSessionTemplateRequest]:
    body: BodyParam[UpdateSessionTemplateRequest] = BodyParam(UpdateSessionTemplateRequest)
    return body.from_body({"payload": payload})


def _template_path() -> PathParam[TemplatePathParam]:
    path: PathParam[TemplatePathParam] = PathParam(TemplatePathParam)
    return path.from_path(UrlMappingMatchInfo({"template_id": str(uuid.uuid4())}, MagicMock()))


class TestCreateSessionTemplate:
    @pytest.mark.parametrize("payload", INVALID_PAYLOADS)
    async def test_rejects_a_payload_that_is_not_a_list_of_templates(
        self,
        handler: SessionTemplateHandler,
        user_ctx: UserContext,
        req_ctx: RequestCtx,
        payload: str,
    ) -> None:
        with pytest.raises(InvalidAPIParameters):
            await handler.create(_create_body(payload), user_ctx, req_ctx)

    async def test_rejects_a_malformed_yaml_payload(
        self,
        handler: SessionTemplateHandler,
        user_ctx: UserContext,
        req_ctx: RequestCtx,
    ) -> None:
        with pytest.raises(InvalidAPIParameters):
            await handler.create(_create_body("template: [unclosed"), user_ctx, req_ctx)

    @pytest.mark.parametrize(
        "payload",
        [
            pytest.param(json.dumps([{"template": TEMPLATE, "name": "t1"}]), id="json-list"),
            pytest.param(
                "template:\n  kind: task_template\nname: t1\n---\ntemplate:\n  kind: task_template\n",
                id="yaml-documents",
            ),
        ],
    )
    async def test_creates_templates_from_a_list_of_templates(
        self,
        handler: SessionTemplateHandler,
        mock_processors: MagicMock,
        user_ctx: UserContext,
        req_ctx: RequestCtx,
        payload: str,
    ) -> None:
        created = CreatedTaskTemplateItem(id=str(uuid.uuid4()), user=str(user_ctx.user_uuid))
        mock_processors.template.create_task.run = AsyncMock(
            return_value=CreateTaskTemplateActionResult(created=[created])
        )

        response = await handler.create(_create_body(payload), user_ctx, req_ctx)

        assert response.status_code == HTTPStatus.OK
        action = mock_processors.template.create_task.run.call_args.args[0]
        assert action.items[0].name == "t1"


class TestUpdateSessionTemplate:
    @pytest.mark.parametrize("payload", INVALID_PAYLOADS)
    async def test_rejects_a_payload_that_is_not_a_list_of_templates(
        self,
        handler: SessionTemplateHandler,
        user_ctx: UserContext,
        req_ctx: RequestCtx,
        payload: str,
    ) -> None:
        with pytest.raises(InvalidAPIParameters):
            await handler.update(_template_path(), _update_body(payload), user_ctx, req_ctx)

    async def test_updates_the_template_from_a_list_of_templates(
        self,
        handler: SessionTemplateHandler,
        mock_processors: MagicMock,
        user_ctx: UserContext,
        req_ctx: RequestCtx,
    ) -> None:
        mock_processors.template.update_task.run = AsyncMock(
            return_value=UpdateTaskTemplateActionResult()
        )
        payload = json.dumps([{"template": TEMPLATE, "name": "t1"}])

        response = await handler.update(_template_path(), _update_body(payload), user_ctx, req_ctx)

        assert response.status_code == HTTPStatus.OK
        action = mock_processors.template.update_task.run.call_args.args[0]
        assert action.items[0].name == "t1"

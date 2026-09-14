"""The entity and field error bases: what they answer with, and that the roots
cannot be constructed."""

from __future__ import annotations

import uuid
from typing import override

import pytest
from aiohttp import web

from ai.backend.common.data.entity.agent import AgentEntityType, AgentUUID
from ai.backend.common.data.entity.audit_log import AuditLogFieldType, AuditLogID
from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.replica import ReplicaFieldType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
    InvalidErrorCode,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.agent import AgentAlreadyExited
from ai.backend.manager.errors.base.entity import (
    EntityError,
    EntityErrorCode,
    EntityNotFoundError,
)
from ai.backend.manager.errors.base.field import FieldError, FieldErrorCode, FieldNotFoundError
from ai.backend.manager.errors.base.not_found import NotFoundError


class _Refused(EntityError, web.HTTPForbidden):
    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            DeploymentEntityType(), ActionOperationType.UPDATE, ErrorDetail.FORBIDDEN
        )


class _SessionRefused(EntityError, web.HTTPForbidden):
    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(SessionEntityType(), ActionOperationType.GET, ErrorDetail.FORBIDDEN)


class _Purged(EntityError, web.HTTPForbidden):
    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            DeploymentEntityType(), ActionOperationType.PURGE, ErrorDetail.FORBIDDEN
        )


class _KernelStuck(FieldError, web.HTTPConflict):
    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            KernelID.field_type(), ActionOperationType.UPDATE, ErrorDetail.CONFLICT
        )


class _ReplicaStuck(FieldError, web.HTTPConflict):
    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(ReplicaFieldType(), ActionOperationType.UPDATE, ErrorDetail.CONFLICT)


class _DanglingRecord(FieldError, web.HTTPConflict):
    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(AuditLogFieldType(), ActionOperationType.GET, ErrorDetail.CONFLICT)


class TestAbstractRootsAreNotConstructible:
    """``Exception.__new__`` skips the abstract check, so the metaclass makes it."""

    @pytest.mark.parametrize("cls", [BackendAIError, NotFoundError, EntityError, FieldError])
    def test_a_root_that_owes_its_code_is_refused(self, cls: type[BackendAIError]) -> None:
        with pytest.raises(TypeError, match="abstract error"):
            cls()

    def test_a_concrete_error_is_built(self) -> None:
        assert _Refused().status_code == 403


class TestEntityError:
    def test_the_answered_triple_forms_the_code(self) -> None:
        assert str(_Refused().error_code()) == "deployment_update_forbidden"

    def test_the_body_carries_the_code_and_the_message(self) -> None:
        err = _SessionRefused("why")
        assert err.body_dict["error_code"] == "session_read_forbidden"
        assert err.body_dict["msg"] == "why"

    def test_the_action_operation_is_mapped(self) -> None:
        assert _Purged().error_code().operation is ErrorOperation.HARD_DELETE
        assert str(_Purged().error_code()) == "deployment_purge_forbidden"

    def test_a_hand_written_error_keeps_its_code(self) -> None:
        err = AgentAlreadyExited(AgentUUID(uuid.uuid4()))
        assert str(err.error_code()) == "agent_update_conflict"

    def test_not_found_takes_the_entity_type(self) -> None:
        err = EntityNotFoundError(
            entity_type=AgentEntityType(), operation=ActionOperationType.PURGE
        )
        assert str(err.error_code()) == "agent_purge_not-found"
        assert err.status_code == 404
        assert isinstance(err, NotFoundError)


class TestFieldError:
    def test_the_owner_and_the_row_form_the_domain(self) -> None:
        assert str(_KernelStuck().error_code()) == "session-kernel_update_conflict"
        assert str(_ReplicaStuck().error_code()) == "deployment-replica_update_conflict"

    def test_a_dangling_row_reports_its_own_type_alone(self) -> None:
        assert str(_DanglingRecord().error_code()) == "audit-log_read_conflict"

    def test_not_found_takes_the_field_type(self) -> None:
        err = FieldNotFoundError(field_type=KernelID.field_type())
        assert str(err.error_code()) == "session-kernel_read_not-found"
        assert err.status_code == 404
        assert isinstance(err, NotFoundError)

    def test_a_dangling_id_answers_the_same_way(self) -> None:
        err = FieldNotFoundError(field_type=AuditLogID.field_type())
        assert str(err.error_code()) == "audit-log_read_not-found"


class TestErrorCodeRoundTrip:
    @pytest.mark.parametrize(
        "code",
        [
            "user_read_not-found",
            "model-deployment_update_forbidden",
            "session-kernel_read_not-found",
            "storage-proxy_request_internal-error",
        ],
    )
    def test_from_str_reverses_str(self, code: str) -> None:
        assert str(ErrorCode.from_str(code)) == code

    def test_a_parsed_domain_compares_with_the_enum(self) -> None:
        assert ErrorCode.from_str("agent_update_conflict").domain == ErrorDomain.AGENT

    def test_a_hyphenated_domain_is_kept_whole(self) -> None:
        parsed = ErrorCode.from_str("model-deployment_update_forbidden")
        assert parsed.domain == "model-deployment"
        assert parsed.operation is ErrorOperation.UPDATE

    @pytest.mark.parametrize(
        "code",
        [
            "read_not-found",
            "user_nope_not-found",
            "model_deployment_update_forbidden",
        ],
    )
    def test_malformed_codes_are_rejected(self, code: str) -> None:
        """The last one is a domain that failed to hyphenate its compound word."""
        with pytest.raises(InvalidErrorCode):
            ErrorCode.from_str(code)

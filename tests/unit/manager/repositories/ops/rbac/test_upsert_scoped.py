"""Integration tests for RBACWriteOps.upsert_scoped with a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import aiohttp.web
import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.data.permission.types import (
    EntityType,
    RBACElementRef,
    RBACElementType,
    ScopeType,
)
from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    UnsupportedCompositePrimaryKeyError,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import IntegrityErrorCheck
from ai.backend.manager.repositories.base.rbac.entity_upserter import (
    ConflictTarget,
    RBACEntityUpserter,
)
from ai.backend.manager.repositories.base.upserter import UpserterSpec
from ai.backend.manager.repositories.ops.rbac.provider import RBACOpsProvider
from ai.backend.testutils.db import with_tables

# ORM cluster registration: an ORM insert triggers configure_mappers() over the whole
# registry, and importing the RBAC ops provider registers RoleRow/UserRoleRow whose string
# relationships resolve against these rows. _ORM_CLUSTER keeps them live.
_ORM_CLUSTER = (
    AgentRow,
    AssociationScopesEntitiesRow,
    DomainRow,
    KeyPairRow,
    KeyPairResourcePolicyRow,
    ObjectPermissionRow,
    PermissionRow,
    RoleRow,
    ScalingGroupForDomainRow,
    UserResourcePolicyRow,
    UserRoleRow,
    UserRow,
)

_ENTITY_NAME = "fragment"
_EXISTING_ROW_ID = UUID("11111111-1111-1111-1111-111111111111")
_USER_SCOPE_ID = "user-scope-1"
_PROJECT_SCOPE_ID = "project-scope-1"


# =============================================================================
# Test Row Models
# =============================================================================


class UpsertScopedTestRow(Base):  # type: ignore[misc]
    """ORM model for upsert_scoped testing: one row per (name, scope_type, scope_id)."""

    __tablename__ = "test_upsert_scoped"
    __table_args__ = (
        sa.UniqueConstraint("name", "scope_type", "scope_id", name="uq_test_upsert_scoped"),
        # NULLs are distinct to a unique constraint, so public rows need their own index.
        sa.Index(
            "uq_test_upsert_scoped_public",
            "name",
            "scope_type",
            unique=True,
            postgresql_where=sa.text("scope_id IS NULL"),
        ),
        {"extend_existing": True},
    )

    id: Mapped[UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    scope_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    scope_id: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    value: Mapped[str] = mapped_column(sa.String(50), nullable=False)


class UpsertScopedFKTestRow(Base):  # type: ignore[misc]
    """ORM model whose self-referencing FK acts as a gate for integrity error testing."""

    __tablename__ = "test_upsert_scoped_fk"
    __table_args__ = (
        sa.UniqueConstraint("name", name="uq_test_upsert_scoped_fk_name"),
        {"extend_existing": True},
    )

    id: Mapped[UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(
        GUID, sa.ForeignKey("test_upsert_scoped_fk.id"), nullable=True
    )


class UpsertScopedCompositePKTestRow(Base):  # type: ignore[misc]
    """ORM model with a composite primary key for testing rejection."""

    __tablename__ = "test_upsert_scoped_composite_pk"
    __table_args__ = {"extend_existing": True}

    tenant_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    value: Mapped[str] = mapped_column(sa.String(50), nullable=False)


# =============================================================================
# Upserter Spec Implementations
# =============================================================================


class ScopedUpserterSpec(UpserterSpec[UpsertScopedTestRow]):
    """Upserts one scoped row, updating only its value on conflict."""

    def __init__(self, scope_type: str, scope_id: str | None, value: str) -> None:
        self._scope_type = scope_type
        self._scope_id = scope_id
        self._value = value

    @property
    @override
    def row_class(self) -> type[UpsertScopedTestRow]:
        return UpsertScopedTestRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "name": _ENTITY_NAME,
            "scope_type": self._scope_type,
            "scope_id": self._scope_id,
            "value": self._value,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"value": self._value}


class _TestUpsertParentMissingError(BackendAIError, aiohttp.web.HTTPBadRequest):
    """Test domain error simulating a rejected FK gate."""

    error_type = "https://api.backend.ai/probs/test-upsert-scoped-parent-missing"
    error_title = "Parent does not exist."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class FKGateUpserterSpec(UpserterSpec[UpsertScopedFKTestRow]):
    """Upserts a row behind a FK gate, mapping the violation to a domain error."""

    def __init__(self, parent_id: UUID) -> None:
        self._parent_id = parent_id

    @property
    @override
    def row_class(self) -> type[UpsertScopedFKTestRow]:
        return UpsertScopedFKTestRow

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=_TestUpsertParentMissingError(extra_msg="parent does not exist"),
            ),
        )

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"name": _ENTITY_NAME, "parent_id": self._parent_id}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"parent_id": self._parent_id}


class CompositePKUpserterSpec(UpserterSpec[UpsertScopedCompositePKTestRow]):
    """Upserter spec for composite PK testing."""

    @property
    @override
    def row_class(self) -> type[UpsertScopedCompositePKTestRow]:
        return UpsertScopedCompositePKTestRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"tenant_id": 1, "item_id": 1, "value": "after"}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"value": "after"}


# =============================================================================
# Cases
# =============================================================================


@dataclass(frozen=True)
class _ScopeBinding:
    scope_type: ScopeType
    scope_id: str


@dataclass(frozen=True)
class _UpsertCase:
    label: str
    scope_type: str
    scope_id: str | None
    scope_ref: RBACElementRef | None
    conflict_target: ConflictTarget
    additional_scope_refs: list[RBACElementRef]
    expected_bindings: list[_ScopeBinding]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def provider(database_connection: ExtendedAsyncSAEngine) -> RBACOpsProvider:
    return RBACOpsProvider(database_connection)


@pytest.fixture
async def create_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with with_tables(
        database_connection, [UpsertScopedTestRow, AssociationScopesEntitiesRow]
    ):
        yield


@pytest.fixture
async def create_fk_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with with_tables(
        database_connection, [UpsertScopedFKTestRow, AssociationScopesEntitiesRow]
    ):
        yield


@pytest.fixture
async def create_composite_pk_table(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with database_connection.begin() as conn:
        await conn.run_sync(
            lambda c: UpsertScopedCompositePKTestRow.__table__.create(c, checkfirst=True)
        )
    yield
    async with database_connection.begin() as conn:
        await conn.run_sync(
            lambda c: UpsertScopedCompositePKTestRow.__table__.drop(c, checkfirst=True)
        )


@pytest.fixture
async def seeded_case(
    database_connection: ExtendedAsyncSAEngine,
    create_tables: None,
    request: pytest.FixtureRequest,
) -> _UpsertCase:
    """Insert the conflicting row and its bindings directly, bypassing the write op."""
    case: _UpsertCase = request.param
    async with database_connection.begin_session() as db_sess:
        await db_sess.execute(
            sa.insert(UpsertScopedTestRow).values(
                id=_EXISTING_ROW_ID,
                name=_ENTITY_NAME,
                scope_type=case.scope_type,
                scope_id=case.scope_id,
                value="before",
            )
        )
        for binding in case.expected_bindings:
            await db_sess.execute(
                sa.insert(AssociationScopesEntitiesRow).values(
                    scope_type=binding.scope_type,
                    scope_id=binding.scope_id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(_EXISTING_ROW_ID),
                )
            )
    return case


# =============================================================================
# Tests
# =============================================================================


class TestUpsertScoped:
    """Insert and conflict paths of RBACWriteOps.upsert_scoped."""

    @pytest.mark.parametrize(
        "case",
        [
            _UpsertCase(
                label="user-scope",
                scope_type="user",
                scope_id=_USER_SCOPE_ID,
                scope_ref=RBACElementRef(RBACElementType.USER, _USER_SCOPE_ID),
                conflict_target=ConflictTarget(columns=["name", "scope_type", "scope_id"]),
                additional_scope_refs=[],
                expected_bindings=[_ScopeBinding(ScopeType.USER, _USER_SCOPE_ID)],
            ),
            _UpsertCase(
                label="project-scope-with-additional-user",
                scope_type="project",
                scope_id=_PROJECT_SCOPE_ID,
                scope_ref=RBACElementRef(RBACElementType.PROJECT, _PROJECT_SCOPE_ID),
                conflict_target=ConflictTarget(columns=["name", "scope_type", "scope_id"]),
                additional_scope_refs=[RBACElementRef(RBACElementType.USER, _USER_SCOPE_ID)],
                expected_bindings=[
                    _ScopeBinding(ScopeType.PROJECT, _PROJECT_SCOPE_ID),
                    _ScopeBinding(ScopeType.USER, _USER_SCOPE_ID),
                ],
            ),
            _UpsertCase(
                label="public-partial-index",
                scope_type="public",
                scope_id=None,
                scope_ref=None,
                conflict_target=ConflictTarget(
                    columns=["name", "scope_type"],
                    partial_index_predicate=UpsertScopedTestRow.scope_id.is_(None),
                ),
                additional_scope_refs=[],
                expected_bindings=[],
            ),
        ],
        ids=lambda case: case.label,
    )
    async def test_insert_binds_new_row(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        create_tables: None,
        case: _UpsertCase,
    ) -> None:
        """An inserted row is bound to every scope the upserter carries."""
        async with provider.write_ops() as w:
            result = await w.upsert_scoped(
                RBACEntityUpserter(
                    spec=ScopedUpserterSpec(case.scope_type, case.scope_id, "after"),
                    element_type=RBACElementType.VFOLDER,
                    scope_ref=case.scope_ref,
                    conflict_target=case.conflict_target,
                    additional_scope_refs=case.additional_scope_refs,
                )
            )

        assert result.row.value == "after"
        assert result.row.scope_id == case.scope_id

        async with database_connection.begin_session_read_committed() as sess:
            rows = (await sess.scalars(sa.select(UpsertScopedTestRow))).all()
            assocs = (await sess.scalars(sa.select(AssociationScopesEntitiesRow))).all()

        assert len(rows) == 1
        assert {_ScopeBinding(a.scope_type, a.scope_id) for a in assocs} == set(
            case.expected_bindings
        )
        assert {a.entity_id for a in assocs} <= {str(result.row.id)}

    @pytest.mark.parametrize(
        "seeded_case",
        [
            _UpsertCase(
                label="user-scope",
                scope_type="user",
                scope_id=_USER_SCOPE_ID,
                scope_ref=RBACElementRef(RBACElementType.USER, _USER_SCOPE_ID),
                conflict_target=ConflictTarget(columns=["name", "scope_type", "scope_id"]),
                additional_scope_refs=[],
                expected_bindings=[_ScopeBinding(ScopeType.USER, _USER_SCOPE_ID)],
            ),
            _UpsertCase(
                label="project-scope-with-additional-user",
                scope_type="project",
                scope_id=_PROJECT_SCOPE_ID,
                scope_ref=RBACElementRef(RBACElementType.PROJECT, _PROJECT_SCOPE_ID),
                conflict_target=ConflictTarget(columns=["name", "scope_type", "scope_id"]),
                additional_scope_refs=[RBACElementRef(RBACElementType.USER, _USER_SCOPE_ID)],
                expected_bindings=[
                    _ScopeBinding(ScopeType.PROJECT, _PROJECT_SCOPE_ID),
                    _ScopeBinding(ScopeType.USER, _USER_SCOPE_ID),
                ],
            ),
            _UpsertCase(
                label="public-partial-index",
                scope_type="public",
                scope_id=None,
                scope_ref=None,
                conflict_target=ConflictTarget(
                    columns=["name", "scope_type"],
                    partial_index_predicate=UpsertScopedTestRow.scope_id.is_(None),
                ),
                additional_scope_refs=[],
                expected_bindings=[],
            ),
        ],
        ids=lambda case: case.label,
        indirect=True,
    )
    async def test_conflict_updates_row_without_duplicating_bindings(
        self,
        database_connection: ExtendedAsyncSAEngine,
        provider: RBACOpsProvider,
        seeded_case: _UpsertCase,
    ) -> None:
        """A conflicting upsert updates the row in place and leaves its bindings as they were."""
        case = seeded_case

        async with provider.write_ops() as w:
            result = await w.upsert_scoped(
                RBACEntityUpserter(
                    spec=ScopedUpserterSpec(case.scope_type, case.scope_id, "after"),
                    element_type=RBACElementType.VFOLDER,
                    scope_ref=case.scope_ref,
                    conflict_target=case.conflict_target,
                    additional_scope_refs=case.additional_scope_refs,
                )
            )

        assert result.row.id == _EXISTING_ROW_ID
        assert result.row.value == "after"

        async with database_connection.begin_session_read_committed() as sess:
            rows = (await sess.scalars(sa.select(UpsertScopedTestRow))).all()
            assocs = (await sess.scalars(sa.select(AssociationScopesEntitiesRow))).all()

        assert len(rows) == 1
        assert rows[0].id == _EXISTING_ROW_ID
        assert rows[0].value == "after"
        assert len(assocs) == len(case.expected_bindings)
        assert {_ScopeBinding(a.scope_type, a.scope_id) for a in assocs} == set(
            case.expected_bindings
        )

    async def test_integrity_error_off_the_conflict_target_raises_domain_error(
        self,
        provider: RBACOpsProvider,
        create_fk_tables: None,
    ) -> None:
        """A FK violation is mapped by the spec's checks instead of being swallowed."""
        with pytest.raises(_TestUpsertParentMissingError, match="parent does not exist"):
            async with provider.write_ops() as w:
                await w.upsert_scoped(
                    RBACEntityUpserter(
                        spec=FKGateUpserterSpec(parent_id=uuid.uuid4()),
                        element_type=RBACElementType.VFOLDER,
                        scope_ref=RBACElementRef(RBACElementType.USER, _USER_SCOPE_ID),
                        conflict_target=ConflictTarget(columns=["name"]),
                    )
                )

    async def test_composite_pk_is_rejected(
        self,
        provider: RBACOpsProvider,
        create_composite_pk_table: None,
    ) -> None:
        """A composite primary key has no single entity id to bind, so it is rejected."""
        with pytest.raises(UnsupportedCompositePrimaryKeyError):
            async with provider.write_ops() as w:
                await w.upsert_scoped(
                    RBACEntityUpserter(
                        spec=CompositePKUpserterSpec(),
                        element_type=RBACElementType.VFOLDER,
                        scope_ref=RBACElementRef(RBACElementType.USER, _USER_SCOPE_ID),
                        conflict_target=ConflictTarget(columns=["tenant_id", "item_id"]),
                    )
                )

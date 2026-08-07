"""RBAC-scoped DB ops: scope-associated entity creation and virtual-scope ownership
on top of the base write ops."""

from __future__ import annotations

import dataclasses
import logging
import uuid
from collections import defaultdict
from collections.abc import AsyncIterator, Collection, Iterable, Mapping, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, ClassVar, Protocol, cast, override

import jinja2
import jinja2.sandbox
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.sql.expression import SQLColumnExpression

from ai.backend.common.data.entity.container_registry import CONTAINER_REGISTRY_SCOPE_TYPE
from ai.backend.common.data.entity.domain import DOMAIN_SCOPE_TYPE
from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE
from ai.backend.common.data.entity.resource_group import RESOURCE_GROUP_SCOPE_TYPE
from ai.backend.common.data.entity.types import EntityRef, EntityType, ScopeRef, ScopeType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, USER_SCOPE_TYPE
from ai.backend.common.data.permission.types import (
    Permission,
    RBACElementType,
)
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.exception import RBACTypeConversionError, UnreachableError
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.common.identifier.scope import ScopeID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.identifier.virtual_scope import VirtualScopeID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.keypair.types import KeyPairCreator, KeyPairSecrets
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.role import ScopeSystemRoleData
from ai.backend.manager.data.permission.scope_template import ScopeTemplateValue
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import (
    EntityType as LegacyEntityType,
)
from ai.backend.manager.data.permission.types import (
    OperationType,
    RBACElementRef,
    RoleSource,
)
from ai.backend.manager.data.permission.types import (
    ScopeType as LegacyScopeType,
)
from ai.backend.manager.errors.permission import VirtualScopeNotFound
from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.errors.role_preset import InvalidRoleNameTemplate
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.keypair import KeyPairRow, generate_keypair_data
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.scaling_group.row import ScalingGroupRow
from ai.backend.manager.models.user import UserRow, UserStatus
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.base import (
    BulkCreator,
    BulkCreatorResult,
    BulkCreatorResultWithFailures,
    Creator,
    CreatorSpec,
    DependentCreatorSpec,
)
from ai.backend.manager.repositories.base.creator import BulkCreatorError
from ai.backend.manager.repositories.base.integrity import (
    match_integrity_error,
    parse_integrity_error,
)
from ai.backend.manager.repositories.base.purger import (
    BulkPurgerError,
    BulkPurgerResultWithFailures,
    validate_conflict_checks,
)
from ai.backend.manager.repositories.base.rbac.entity.creator import EntityCreator
from ai.backend.manager.repositories.base.rbac.entity.purger import (
    EntityBatchPurger,
    EntityBatchPurgerResult,
    EntityPurger,
    EntityPurgerResult,
)
from ai.backend.manager.repositories.base.rbac.entity.types import ScopeMembership
from ai.backend.manager.repositories.base.rbac.entity_creator import (
    RBACBulkEntityCreatorResult,
    RBACBulkEntityCreatorResultWithFailures,
    RBACEntityCreator,
    RBACEntityCreatorResult,
    execute_rbac_entity_creator,
    execute_rbac_entity_creators,
)
from ai.backend.manager.repositories.base.rbac.entity_purger import (
    RBACEntityPurger,
    RBACEntityPurgerResult,
    execute_rbac_entity_purger,
)
from ai.backend.manager.repositories.base.rbac.entity_upserter import (
    RBACEntityUpserter,
    RBACEntityUpserterResult,
)
from ai.backend.manager.repositories.base.rbac.utils import bulk_insert_on_conflict_do_nothing
from ai.backend.manager.repositories.keypair.creators import KeyPairCreatorSpec
from ai.backend.manager.repositories.ops.base.provider import DBOpsProvider, WriteOps
from ai.backend.manager.repositories.permission_controller.creators import (
    AssociationScopesEntitiesCreatorSpec,
    EntityMembershipCreatorSpec,
    PermissionCreatorSpec,
    RoleCreatorSpec,
    ScopeBindingCreatorSpec,
    UserRoleCreatorSpec,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Rendered names are stored in ``roles.name`` (sa.String(64)).
MAX_ROLE_NAME_LENGTH = 64


@dataclass(frozen=True)
class _RoleSpec:
    scope: ScopeRef
    creator: RoleCreatorSpec
    entity_operations: Mapping[RBACElementType, Iterable[OperationType]]


@dataclass
class ScopeCreationResult[TRow: Base]:
    """A created scope row."""

    row: TRow


@dataclass
class FullUserCreation:
    """Everything needed to provision a user in full: the user-scope creation, the
    scopes to enroll in, and the default keypair's policy. ``keypair_secrets`` overrides
    the generated key material (e.g. pre-issued keys)."""

    creation: EntityCreator[UserRow]
    domain_id: DomainID
    project_ids: Collection[ProjectID]
    keypair_resource_policy: str
    keypair_rate_limit: int
    keypair_secrets: KeyPairSecrets | None = None


@dataclass
class FullUserCreationResult:
    """A fully provisioned user: the row (``main_access_key`` set) and its default keypair."""

    user_row: UserRow
    keypair_row: KeyPairRow


@dataclass
class ScopeUserMember(ScopeMembership):
    """A user joining ``target_scope``; membership always grants the scope's
    ``auto_assign`` roles (idempotently), so membership and role state cannot
    drift apart."""

    target_scope: ScopeRef
    user_id: UserID
    cap: Permission | None = None

    @override
    def scope(self) -> ScopeRef:
        return self.target_scope

    @override
    def entity_ref(self) -> EntityRef:
        return EntityRef(entity_type=USER_ENTITY_TYPE, entity_id=self.user_id)

    @override
    def permission_cap(self) -> Permission | None:
        return self.cap

    @override
    def assign_role_on(self) -> UserID:
        return self.user_id


@dataclass
class ScopeEntityMember(ScopeMembership):
    """A non-user entity joining ``target_scope``; no roles are granted for it."""

    target_scope: ScopeRef
    ref: EntityRef
    cap: Permission | None = None

    @override
    def scope(self) -> ScopeRef:
        return self.target_scope

    @override
    def entity_ref(self) -> EntityRef:
        return self.ref

    @override
    def permission_cap(self) -> Permission | None:
        return self.cap

    @override
    def assign_role_on(self) -> UserID | None:
        return None


@dataclass
class EntityMemberCreationError:
    """A membership whose addition failed, with the exception that rolled it back."""

    membership: ScopeMembership
    exception: Exception
    index: int


@dataclass
class EntityMembersResultWithFailures:
    successes: list[ScopeMembership]
    errors: list[EntityMemberCreationError]


@dataclass
class _RBACCleanupCounts:
    """Row counts of an entity purge's RBAC cleanup."""

    permission_count: int
    scope_association_count: int


class ScopeSource(Protocol):
    """A Row queryable as an RBAC scope: its scope-id and display-name expressions."""

    @classmethod
    def scope_id_expr(cls) -> SQLColumnExpression[ScopeID]:
        """Column whose value is used as ``ScopeRef.scope_id``."""
        ...

    @classmethod
    def scope_name_expr(cls) -> SQLColumnExpression[str]:
        """Expression rendering the scope's display name."""
        ...


class RBACWriteOps(WriteOps):
    """Base write ops plus RBAC scope-associated creation and virtual-scope writes."""

    _scope_rows: ClassVar[Mapping[ScopeType, type[ScopeSource]]] = {
        CONTAINER_REGISTRY_SCOPE_TYPE: ContainerRegistryRow,
        DOMAIN_SCOPE_TYPE: DomainRow,
        PROJECT_SCOPE_TYPE: GroupRow,
        RESOURCE_GROUP_SCOPE_TYPE: ScalingGroupRow,
        USER_SCOPE_TYPE: UserRow,
    }

    def __init__(self, sess: SASession) -> None:
        super().__init__(sess)
        self._template_env = jinja2.sandbox.ImmutableSandboxedEnvironment(
            undefined=jinja2.StrictUndefined,
        )

    async def _resolve_scope_template_values(
        self, scopes: Collection[ScopeRef]
    ) -> dict[ScopeRef, ScopeTemplateValue | None]:
        """Resolve the scope attributes exposed to role name templates with a
        single UNION ALL query over the registered scope rows.

        Scopes of unregistered types or whose row is gone map to None.
        """
        names: dict[ScopeRef, str | None] = dict.fromkeys(scopes)
        ids_by_type: dict[ScopeType, list[ScopeID]] = defaultdict(list)
        for s in scopes:
            ids_by_type[s.scope_type].append(s.scope_id)
        selects: list[sa.Select[tuple[str, ScopeID, str]]] = []
        for scope_type, ids in ids_by_type.items():
            row_cls = self._scope_rows.get(scope_type)
            if row_cls is None:
                continue
            selects.append(
                sa.select(
                    sa.literal(str(scope_type)),
                    row_cls.scope_id_expr(),
                    row_cls.scope_name_expr(),
                ).where(row_cls.scope_id_expr().in_(ids))
            )
        if selects:
            result = await self._sess.execute(sa.union_all(*selects))
            for scope_type_value, scope_id, scope_name in result.tuples():
                ref = ScopeRef(
                    scope_type=ScopeType(scope_type_value),
                    scope_id=scope_id,
                )
                names[ref] = scope_name
        return {
            scope: (
                ScopeTemplateValue(
                    id=scope.scope_id,
                    name=name,
                    type=str(scope.scope_type),
                )
                if name is not None
                else None
            )
            for scope, name in names.items()
        }

    def _render_role_name(self, template: str, scope: ScopeTemplateValue) -> str:
        """Render a role name from a preset's ``role_name_template`` (e.g.
        ``{{scope.type}}-{{scope.name}}-member``), raising :class:`InvalidRoleNameTemplate`
        on syntax errors, undefined variables, or an unusable result."""
        try:
            rendered = self._template_env.from_string(template).render(
                scope=dataclasses.asdict(scope),
            )
        except jinja2.TemplateError as e:
            raise InvalidRoleNameTemplate(f"Failed to render role name template: {e}") from e
        rendered = rendered.strip()
        if not rendered:
            raise InvalidRoleNameTemplate("Role name template rendered to an empty string.")
        if len(rendered) > MAX_ROLE_NAME_LENGTH:
            raise InvalidRoleNameTemplate(
                f"Rendered role name exceeds {MAX_ROLE_NAME_LENGTH} characters: {rendered!r}"
            )
        return rendered

    def validate_role_name_template(self, template: str) -> None:
        """Validate a preset's ``role_name_template`` by rendering it against
        representative dummy values, so syntax errors and undefined variables
        are rejected before the preset is stored."""
        dummy = ScopeTemplateValue(
            id=uuid.UUID(int=0),
            name="name",
            type="user",
        )
        self._render_role_name(template, dummy)

    # -- Spec-based idempotent inserts --------------------------------------------

    async def _bulk_create_ignore_conflicts[TRow: Base](
        self, specs: Sequence[CreatorSpec[TRow]]
    ) -> None:
        """Insert rows from ``specs`` in one statement, skipping rows that conflict
        with existing ones (``ON CONFLICT DO NOTHING``); existing rows are kept as-is."""
        await bulk_insert_on_conflict_do_nothing(self._sess, [spec.build_row() for spec in specs])

    async def _bulk_create_dependent_ignore_conflicts[TDependency, TRow: Base](
        self,
        specs: Sequence[DependentCreatorSpec[TDependency, TRow]],
        dependency: TDependency,
    ) -> None:
        """Insert dependency-resolved rows from ``specs``, skipping rows that conflict
        with existing ones (``ON CONFLICT DO NOTHING``); existing rows are kept as-is."""
        await bulk_insert_on_conflict_do_nothing(
            self._sess, [spec.build_row(dependency) for spec in specs]
        )

    # -- Virtual-scope helpers ----------------------------------------------------

    async def _find_virtual_scope_id(self, scope: ScopeRef) -> VirtualScopeID | None:
        """Return the virtual scope id backing ``scope``, or ``None`` if it has none."""
        stmt = sa.select(VirtualScopeRow.id).where(
            VirtualScopeRow.scope_type == scope.scope_type,
            VirtualScopeRow.scope_id == scope.scope_id,
        )
        return (await self._sess.execute(stmt)).scalar_one_or_none()

    async def _resolve_virtual_scope_id(self, scope: ScopeRef) -> VirtualScopeID:
        """Return the virtual scope id backing ``scope``.

        Every owner scope is created with its virtual scope, so a missing one is an
        invariant violation: raises :class:`VirtualScopeNotFound` (500).
        """
        virtual_scope_id = await self._find_virtual_scope_id(scope)
        if virtual_scope_id is None:
            raise VirtualScopeNotFound(
                f"No virtual scope for scope {scope.scope_type}:{scope.scope_id}"
            )
        return virtual_scope_id

    async def _find_virtual_scope_ids(
        self, scopes: Sequence[ScopeRef]
    ) -> dict[ScopeRef, VirtualScopeID]:
        """Return the virtual scope ids backing ``scopes`` in one query; scopes
        without one are absent from the result."""
        if not scopes:
            return {}
        stmt = sa.select(
            VirtualScopeRow.scope_type,
            VirtualScopeRow.scope_id,
            VirtualScopeRow.id,
        ).where(
            sa.tuple_(VirtualScopeRow.scope_type, VirtualScopeRow.scope_id).in_([
                (s.scope_type, s.scope_id) for s in scopes
            ])
        )
        return {
            ScopeRef(scope_type=ScopeType(row.scope_type), scope_id=row.scope_id): row.id
            for row in (await self._sess.execute(stmt)).all()
        }

    async def _resolve_virtual_scope_ids(
        self, scopes: Sequence[ScopeRef]
    ) -> dict[ScopeRef, VirtualScopeID]:
        """Return the virtual scope id backing each of ``scopes`` in one query.

        As with :meth:`_resolve_virtual_scope_id`, a scope without a virtual scope is
        an invariant violation: raises :class:`VirtualScopeNotFound` naming them all.
        """
        resolved = await self._find_virtual_scope_ids(scopes)
        missing = [s for s in scopes if s not in resolved]
        if missing:
            raise VirtualScopeNotFound(
                "No virtual scope for scopes: "
                + ", ".join(f"{s.scope_type}:{s.scope_id}" for s in missing)
            )
        return resolved

    async def _insert_virtual_scopes(self, scopes: Sequence[ScopeRef]) -> None:
        """Create each scope's virtual scope node with its self entity-membership and self
        scope_binding (permission_cap NULL). Idempotent: an existing scope is a no-op."""
        if not scopes:
            return
        values = [{"scope_type": s.scope_type, "scope_id": s.scope_id} for s in scopes]
        insert_stmt = (
            pg_insert(VirtualScopeRow)
            .values(values)
            .on_conflict_do_nothing(index_elements=["scope_type", "scope_id"])
            .returning(
                VirtualScopeRow.id,
                VirtualScopeRow.scope_type,
                VirtualScopeRow.scope_id,
            )
        )
        inserted = (await self._sess.execute(insert_stmt)).all()
        if not inserted:
            return
        membership_stmt = (
            pg_insert(EntityMembershipRow)
            .values([
                {
                    "virtual_scope_id": row.id,
                    "entity_type": row.scope_type,
                    "entity_id": row.scope_id,
                    "permission_cap": None,
                }
                for row in inserted
            ])
            .on_conflict_do_nothing()
        )
        await self._sess.execute(membership_stmt)
        binding_stmt = (
            pg_insert(ScopeBindingRow)
            .values([
                {
                    "virtual_scope_id": row.id,
                    "scope_type": row.scope_type,
                    "scope_id": row.scope_id,
                    "permission_cap": None,
                }
                for row in inserted
            ])
            .on_conflict_do_nothing()
        )
        await self._sess.execute(binding_stmt)

    async def _delete_virtual_scopes(self, scopes: Sequence[ScopeRef]) -> None:
        """Delete the virtual scope nodes for ``scopes`` (FK CASCADE removes the edges
        inside them), plus the edges the scopes left in other virtual scopes — bindings
        where a deleted scope is the reaching side and memberships where it is enrolled
        as an entity — which no FK covers."""
        if not scopes:
            return
        scope_keys = [(s.scope_type, s.scope_id) for s in scopes]
        await self._sess.execute(
            sa.delete(VirtualScopeRow).where(
                sa.tuple_(VirtualScopeRow.scope_type, VirtualScopeRow.scope_id).in_(scope_keys)
            )
        )
        await self._sess.execute(
            sa.delete(ScopeBindingRow).where(
                sa.tuple_(ScopeBindingRow.scope_type, ScopeBindingRow.scope_id).in_(scope_keys)
            )
        )
        await self._sess.execute(
            sa.delete(EntityMembershipRow).where(
                sa.tuple_(EntityMembershipRow.entity_type, EntityMembershipRow.entity_id).in_(
                    scope_keys
                )
            )
        )

    async def create_scoped[TRow: Base](
        self,
        creator: RBACEntityCreator[TRow],
    ) -> RBACEntityCreatorResult[TRow]:
        """Insert one row with its RBAC scope association (the creator carries its scope).

        Deprecated: keys on the legacy element types; new code uses
        :class:`EntityCreator` via the ``_scope()`` methods.
        """
        return await execute_rbac_entity_creator(self._sess, creator)

    async def upsert_scoped[TRow: Base](
        self,
        upserter: RBACEntityUpserter[TRow],
    ) -> RBACEntityUpserterResult[TRow]:
        """Upsert one row (INSERT ON CONFLICT UPDATE) with its RBAC scope association.

        Deprecated: keys on the legacy element types; new code uses
        :class:`EntityUpserter`.

        The upsert counterpart of :meth:`create_scoped`; see :class:`RBACEntityUpserter` for
        the conflict target it requires.
        """
        spec = upserter.spec
        row_class = spec.row_class
        table = row_class.__table__
        pk_columns = sa.inspect(row_class).primary_key
        if len(pk_columns) != 1:
            raise UnsupportedCompositePrimaryKeyError(
                f"Entity upserter only supports single-column primary keys (table: {table.name})",
            )

        stmt = (
            pg_insert(table)
            .values(spec.build_insert_values())
            .on_conflict_do_update(
                index_elements=upserter.conflict_target.columns,
                index_where=upserter.conflict_target.index_predicate,
                set_=spec.build_update_values(),
            )
            .returning(*table.columns)
        )
        try:
            result = await self._sess.execute(stmt)
        except sa.exc.IntegrityError as e:
            # The conflict target is an update, so this is another constraint (a FK gate, say).
            match_integrity_error(parse_integrity_error(e), spec.integrity_error_checks)
        else:
            row_data = result.fetchone()

        if row_data is None:
            raise UnreachableError("ON CONFLICT DO UPDATE returns the inserted or updated row")
        row: TRow = row_class(**dict(row_data._mapping))

        entity_type = upserter.element_type.to_entity_type()
        pk_value = row_data._mapping[pk_columns[0].name]
        await bulk_insert_on_conflict_do_nothing(
            self._sess,
            [
                AssociationScopesEntitiesRow(
                    scope_type=scope_ref.element_type.to_scope_type(),
                    scope_id=scope_ref.element_id,
                    entity_type=entity_type,
                    entity_id=str(pk_value),
                    relation_type=upserter.relation_type,
                )
                for scope_ref in upserter.all_scope_refs()
            ],
        )
        return RBACEntityUpserterResult(row=row)

    async def bulk_create_scoped[TRow: Base](
        self,
        creators: Sequence[RBACEntityCreator[TRow]],
    ) -> RBACBulkEntityCreatorResult[TRow]:
        """Insert rows with their RBAC scope associations (each creator carries its scope).

        Deprecated: keys on the legacy element types; new code uses
        :class:`EntityCreator` via the ``_scope()`` methods.
        """
        return await execute_rbac_entity_creators(self._sess, creators)

    async def bulk_create_scoped_partial[TRow: Base](
        self,
        creators: Sequence[RBACEntityCreator[TRow]],
    ) -> RBACBulkEntityCreatorResultWithFailures[TRow]:
        """Insert rows with their scope associations, isolating each row for partial success.

        Deprecated: keys on the legacy element types; new code uses
        :class:`EntityCreator` via the ``_scope()`` methods.

        The scoped counterpart of :meth:`bulk_create_partial`: a row and its association share
        one savepoint, so a rejected row rolls back both and leaves the rest created.
        :meth:`bulk_create_scoped` flushes the batch at once instead and is all-or-nothing.
        """
        successes: list[TRow] = []
        errors: list[BulkCreatorError[TRow]] = []
        for index, creator in enumerate(creators):
            # The handlers stay outside the savepoint: a failure has to reach the context
            # manager for it to roll back. Catching inside would leave it releasing a
            # savepoint the failed statement already aborted, which kills the whole batch.
            try:
                async with self.savepoint():
                    result = await execute_rbac_entity_creator(self._sess, creator)
                successes.append(result.row)
            except sa.exc.IntegrityError as e:
                errors.append(
                    BulkCreatorError(
                        spec=creator.spec, exception=parse_integrity_error(e), index=index
                    )
                )
            except Exception as e:
                # execute_rbac_entity_creator maps the integrity errors its spec declares
                # onto domain errors; whatever arrives here fails just this row.
                errors.append(BulkCreatorError(spec=creator.spec, exception=e, index=index))
        return RBACBulkEntityCreatorResultWithFailures(successes=successes, errors=errors)

    async def purge_scoped[TRow: Base](
        self,
        purger: RBACEntityPurger[TRow],
    ) -> RBACEntityPurgerResult[TRow] | None:
        """Delete one row and its RBAC entries; ``None`` if the row is already gone.

        Deprecated: keys on the legacy element types; new code uses
        :class:`EntityPurger` via :meth:`delete_scope`.
        """
        return await execute_rbac_entity_purger(self._sess, purger)

    async def bulk_purge_scoped_partial[TRow: Base](
        self,
        purgers: Sequence[RBACEntityPurger[TRow]],
    ) -> BulkPurgerResultWithFailures[TRow]:
        """Delete rows with their RBAC entries, isolating each row for partial success.

        Deprecated: keys on the legacy element types; new code uses
        :class:`EntityPurger` via the ``_scope()`` methods.

        The scoped counterpart of :meth:`bulk_purge_partial`: a row and its RBAC entries share
        one savepoint, so a failed row rolls back both and leaves the rest deleted. A purger
        targeting a row that is already gone is skipped — no success, no error.
        """
        successes: list[TRow] = []
        errors: list[BulkPurgerError[TRow]] = []
        for index, purger in enumerate(purgers):
            # The handler stays outside the savepoint — see bulk_create_scoped_partial.
            try:
                async with self.savepoint():
                    result = await execute_rbac_entity_purger(self._sess, purger)
                if result is not None:
                    successes.append(result.row)
            except Exception as e:
                errors.append(BulkPurgerError(purger=purger, exception=e, index=index))
        return BulkPurgerResultWithFailures(successes=successes, errors=errors)

    # -- Scope lifecycle: real scope entity + its virtual scope node --------------

    async def create_scope[TRow: Base](
        self,
        creation: EntityCreator[TRow],
    ) -> ScopeCreationResult[TRow]:
        """Create a scope in full: the real row, its virtual scope node, the
        membership edges its creator declares (each writing the scope association and
        virtual-scope edges), its SYSTEM roles, and the roles from matching presets.

        The row is inserted first, so ``creation`` sees the id the database assigned.
        The roles are only created here; membership-driven role grants go through
        :meth:`add_bulk_members`.
        """
        result = await self.create(Creator(spec=creation.spec()))
        scope = self._member_scope_ref(creation.entity_ref_of(result.row))
        await self._insert_virtual_scopes([scope])
        await self.add_bulk_members(creation.membership(result.row))
        await self._provision_scope_roles({scope: creation.system_roles_of(result.row)})
        return ScopeCreationResult(row=result.row)

    async def bulk_create_scopes[TRow: Base](
        self,
        creations: Sequence[EntityCreator[TRow]],
    ) -> BulkCreatorResult[TRow]:
        """Create multiple scopes in full, as :meth:`create_scope` does for one.

        The real scope rows are created atomically via a single bulk insert: either
        all rows are materialized, or the whole batch fails and nothing is created.
        The virtual scope inserts are idempotent (get-or-create), and the whole
        batch's membership edges are enrolled in one :meth:`add_bulk_members` call.
        """
        result = await self.bulk_create(BulkCreator(specs=[c.spec() for c in creations]))
        scope_roles = {
            self._member_scope_ref(creation.entity_ref_of(row)): creation.system_roles_of(row)
            for creation, row in zip(creations, result.rows, strict=True)
        }
        await self._insert_virtual_scopes(list(scope_roles.keys()))
        await self.add_bulk_members([
            membership
            for creation, row in zip(creations, result.rows, strict=True)
            for membership in creation.membership(row)
        ])
        await self._provision_scope_roles(scope_roles)
        return result

    async def bulk_create_scopes_partial[TRow: Base](
        self,
        creations: Sequence[EntityCreator[TRow]],
    ) -> BulkCreatorResultWithFailures[TRow]:
        """Create scopes as :meth:`create_scope` does, isolating each creation in its
        own savepoint: a failed creation — its row, virtual scope, memberships, or
        roles — rolls back whole and lands in ``errors`` while the rest are fully
        created. ``errors`` index into ``creations``.
        """
        successes: list[TRow] = []
        errors: list[BulkCreatorError[TRow]] = []
        for index, creation in enumerate(creations):
            # The handlers stay outside the savepoint — see bulk_create_scoped_partial.
            try:
                async with self.savepoint():
                    result = await self.create_scope(creation)
                successes.append(result.row)
            except sa.exc.IntegrityError as e:
                errors.append(
                    BulkCreatorError(
                        spec=creation.spec(), exception=parse_integrity_error(e), index=index
                    )
                )
            except Exception as e:
                # create_scope maps the integrity errors its spec declares onto domain
                # errors; whatever arrives here fails just this creation.
                errors.append(BulkCreatorError(spec=creation.spec(), exception=e, index=index))
        return BulkCreatorResultWithFailures(successes=successes, errors=errors)

    # -- Scope lifecycle: roles provisioned with the scope ------------------------

    @staticmethod
    def _scope_element_type(scope: ScopeRef) -> RBACElementType:
        try:
            return RBACElementType(scope.scope_type)
        except ValueError as e:
            raise RBACTypeConversionError(
                f"Scope type {scope.scope_type!r} has no corresponding RBAC element type"
            ) from e

    @staticmethod
    def _system_role_specs(
        scope_roles: Mapping[ScopeRef, Collection[ScopeSystemRoleData]],
    ) -> list[_RoleSpec]:
        return [
            _RoleSpec(
                scope=scope,
                creator=RoleCreatorSpec(
                    name=role_data.role_name(),
                    source=RoleSource.SYSTEM,
                    status=RoleStatus.ACTIVE,
                    # A user scope's system role is auto-assigned: its only member is
                    # the user itself, who always holds its own role. Declared roles
                    # of container scopes (admin/member) are granted explicitly.
                    auto_assign=scope.scope_type == USER_SCOPE_TYPE,
                ),
                entity_operations=role_data.entity_operations(),
            )
            for scope, role_datas in scope_roles.items()
            for role_data in role_datas
        ]

    async def _provision_scope_roles(
        self,
        scope_roles: Mapping[ScopeRef, Collection[ScopeSystemRoleData]],
    ) -> list[RoleRow]:
        """Create every scope's declared SYSTEM roles and its preset-derived roles.

        Whatever the number of scopes and roles, this issues one insert for all the roles
        and one for all their permissions. Returns the created roles.
        """
        role_specs = self._system_role_specs(scope_roles)
        preset_role_specs = await self._preset_role_specs(scope_roles.keys())
        specs = [*role_specs, *preset_role_specs]
        if not specs:
            return []
        return await self._create_roles(specs)

    async def _preset_role_specs(self, scopes: Collection[ScopeRef]) -> list[_RoleSpec]:
        """The roles the active presets matching ``scopes``' types call for."""
        if not scopes:
            return []
        preset_rows = (
            await self._sess.scalars(
                sa.select(RolePresetRow).where(
                    RolePresetRow.scope_type.in_({
                        self._scope_element_type(scope).to_scope_type() for scope in scopes
                    }),
                    RolePresetRow.deleted.is_(False),
                )
            )
        ).all()
        if not preset_rows:
            return []
        operations_by_preset: dict[RolePresetID, dict[RBACElementType, list[OperationType]]] = (
            defaultdict(lambda: defaultdict(list))
        )
        preset_permission_rows = (
            await self._sess.scalars(
                sa.select(RolePermissionPresetRow).where(
                    RolePermissionPresetRow.role_preset_id.in_([
                        preset.id for preset in preset_rows
                    ])
                )
            )
        ).all()
        for preset_permission in preset_permission_rows:
            operations_by_preset[preset_permission.role_preset_id][
                preset_permission.entity_type.to_element()
            ].append(preset_permission.operation)
        presets_by_scope_type: dict[LegacyScopeType, list[RolePresetRow]] = defaultdict(list)
        for preset in preset_rows:
            presets_by_scope_type[preset.scope_type].append(preset)
        scope_template_values: dict[ScopeRef, ScopeTemplateValue | None] = {}
        if any(preset.role_name_template is not None for preset in preset_rows):
            scope_template_values = await self._resolve_scope_template_values(scopes)
        return [
            _RoleSpec(
                scope=scope,
                creator=RoleCreatorSpec(
                    name=self._render_preset_role_name(
                        preset, scope, scope_template_values.get(scope)
                    ),
                    source=RoleSource.SYSTEM,
                    status=RoleStatus.ACTIVE,
                    auto_assign=preset.auto_assign,
                ),
                entity_operations=operations_by_preset[preset.id],
            )
            for scope in scopes
            for preset in presets_by_scope_type[self._scope_element_type(scope).to_scope_type()]
        ]

    @staticmethod
    def _fallback_preset_role_name(scope: ScopeRef) -> str:
        """Deterministic per-scope role name used when a preset's template cannot
        be rendered. Built with plain string formatting — never via the template
        engine — so scope creation cannot fail on role naming."""
        return f"{scope.scope_type}-{str(scope.scope_id)[:8]}-role"

    def _render_preset_role_name(
        self,
        preset: RolePresetRow,
        scope: ScopeRef,
        scope_template_value: ScopeTemplateValue | None,
    ) -> str:
        """Render the name of a role instantiated from the preset, falling back to
        ``{scope_type}-{scope_id[:8]}-role`` so that scope creation never fails on a
        bad template."""
        if preset.role_name_template is None:
            return preset.name
        if scope_template_value is None:
            fallback = self._fallback_preset_role_name(scope)
            log.warning(
                "Cannot resolve scope attributes for role preset {} ({}); falling back to {}",
                preset.id,
                preset.role_name_template,
                fallback,
            )
            return fallback
        try:
            return self._render_role_name(preset.role_name_template, scope_template_value)
        except InvalidRoleNameTemplate as e:
            fallback = self._fallback_preset_role_name(scope)
            log.warning(
                "Failed to render role name template of preset {} ({}): {}; falling back to {}",
                preset.id,
                preset.role_name_template,
                e,
                fallback,
            )
            return fallback

    async def _create_roles(self, specs: Sequence[_RoleSpec]) -> list[RoleRow]:
        """Create ``specs`` and the permissions they grant: one insert for each."""
        if not specs:
            return []
        roles = await self.bulk_create_scoped([
            RBACEntityCreator(
                spec=spec.creator,
                element_type=RBACElementType.ROLE,
                scope_ref=RBACElementRef(
                    element_type=self._scope_element_type(spec.scope),
                    element_id=str(spec.scope.scope_id),
                ),
            )
            for spec in specs
        ])
        permissions = [
            PermissionCreatorSpec(
                role_id=row.id,
                scope_type=self._scope_element_type(spec.scope),
                scope_id=str(spec.scope.scope_id),
                entity_type=entity_type,
                operation=operation,
            )
            for spec, row in zip(specs, roles.rows, strict=True)
            for entity_type, operations in spec.entity_operations.items()
            for operation in operations
        ]
        if permissions:
            await self.bulk_create(BulkCreator(specs=permissions))
        return list(roles.rows)

    async def delete_scope[TRow: Base](
        self,
        purger: EntityPurger[TRow],
    ) -> EntityPurgerResult[TRow] | None:
        """Delete a scope in full: the real row with its RBAC entries (permissions and
        scope associations in both directions) and its virtual scope node, derived
        from the purger spec's entity ref (every entity doubles as a scope).

        Deleting the virtual scope cascades to its scope bindings and entity
        memberships (FK ``ON DELETE CASCADE``); the scope's own bindings and
        memberships in other virtual scopes are deleted explicitly. The virtual scope
        is dropped even if the row is already gone (``None`` is returned).
        """
        result = await self._purge_entity(purger)
        await self._delete_virtual_scopes([self._member_scope_ref(purger.spec.entity_ref())])
        return result

    async def batch_delete_scopes[TRow: Base](
        self,
        purger: EntityBatchPurger[TRow],
    ) -> EntityBatchPurgerResult:
        """Delete the scopes matched by ``purger`` in full, as :meth:`delete_scope`
        does for one.

        The real scope rows are purged in batches with their RBAC entries; each
        deleted row's virtual scope — derived from the spec's entity type and the
        row's primary key — is dropped with its batch (FK ``ON DELETE CASCADE``
        removes its edges) along with the scope's bindings and memberships in other
        virtual scopes.
        """
        return await self._batch_purge_entities(purger, drop_virtual_scopes=True)

    # -- Entity purge execution (association/permission tables still key on the
    # -- legacy enums, so the refs are converted at this SQL boundary) -------------

    @staticmethod
    def _legacy_scope_type(scope_type: ScopeType) -> LegacyScopeType:
        try:
            return LegacyScopeType(scope_type)
        except ValueError as e:
            raise RBACTypeConversionError(
                f"Scope type {scope_type!r} has no legacy RBAC scope type"
            ) from e

    @staticmethod
    def _legacy_entity_type(entity_type: EntityType) -> LegacyEntityType:
        try:
            return LegacyEntityType(entity_type)
        except ValueError as e:
            raise RBACTypeConversionError(
                f"Entity type {entity_type!r} has no legacy RBAC entity type"
            ) from e

    async def _delete_rbac_for_entities(
        self,
        entity_type: EntityType,
        entity_ids: Collection[str],
    ) -> _RBACCleanupCounts:
        """Delete the entities' RBAC entries: permissions where an entity is the scope
        (entity-as-scope pattern), and scope associations in both directions."""
        if not entity_ids:
            return _RBACCleanupCounts(permission_count=0, scope_association_count=0)
        legacy_scope_type = self._legacy_scope_type(ScopeType(entity_type))
        legacy_entity_type = self._legacy_entity_type(entity_type)
        perm_result = await self._sess.execute(
            sa.delete(PermissionRow).where(
                PermissionRow.scope_type == legacy_scope_type,
                PermissionRow.scope_id.in_(entity_ids),
            )
        )
        assoc_result = await self._sess.execute(
            sa.delete(AssociationScopesEntitiesRow).where(
                sa.or_(
                    sa.and_(
                        AssociationScopesEntitiesRow.entity_type == legacy_entity_type,
                        AssociationScopesEntitiesRow.entity_id.in_(entity_ids),
                    ),
                    sa.and_(
                        AssociationScopesEntitiesRow.scope_type == legacy_scope_type,
                        AssociationScopesEntitiesRow.scope_id.in_(entity_ids),
                    ),
                )
            )
        )
        return _RBACCleanupCounts(
            permission_count=cast(CursorResult[Any], perm_result).rowcount or 0,
            scope_association_count=cast(CursorResult[Any], assoc_result).rowcount or 0,
        )

    async def _delete_row_by_pk_returning[TRow: Base](
        self,
        purger: EntityPurger[TRow],
    ) -> TRow | None:
        """Delete the target row by primary key and return the deleted row, or ``None``
        if it is already gone.

        Raises:
            RepositoryIntegrityError: If the DELETE violates a database constraint
                (e.g. a referencing FK with ``ondelete='RESTRICT'``), parsed so callers
                can match on the structured error type and constraint name.
        """
        row_class = purger.spec.row_class()
        table = row_class.__table__
        pk_columns = list(table.primary_key.columns)
        if len(pk_columns) != 1:
            raise UnsupportedCompositePrimaryKeyError(
                f"Purger only supports single-column primary keys (table: {table.name})",
            )
        stmt = (
            sa.delete(table)
            .where(pk_columns[0] == purger.spec.pk_value())
            .returning(*table.columns)
        )
        try:
            result = await self._sess.execute(stmt)
        except sa.exc.IntegrityError as e:
            raise parse_integrity_error(e) from e
        row_data = result.fetchone()
        if row_data is None:
            return None
        return cast(TRow, row_class(**dict(row_data._mapping)))

    async def _purge_entity[TRow: Base](
        self,
        purger: EntityPurger[TRow],
    ) -> EntityPurgerResult[TRow] | None:
        """Delete one entity row by primary key together with its RBAC entries.

        Conflict checks run first, then the RBAC entries are removed, then the row
        itself (RETURNING). Returns ``None`` if the row is already gone.
        """
        ref = purger.spec.entity_ref()
        await validate_conflict_checks(self._sess, purger.spec.conflict_checks())
        await self._delete_rbac_for_entities(ref.entity_type, [str(ref.entity_id)])
        row = await self._delete_row_by_pk_returning(purger)
        if row is None:
            return None
        return EntityPurgerResult(row=row)

    async def _batch_purge_entities[TRow: Base](
        self,
        purger: EntityBatchPurger[TRow],
        *,
        drop_virtual_scopes: bool = False,
    ) -> EntityBatchPurgerResult:
        """Delete the rows matched by the spec in batches, cleaning up each batch's
        RBAC entries, and return the deletion counts.

        With ``drop_virtual_scopes``, each deleted row's virtual scope — derived from
        the spec's entity type and the row's primary key — is dropped with its batch.
        """
        total_deleted = 0
        total_perm = 0
        total_assoc = 0

        base_subquery = purger.spec.build_subquery()
        table = cast(sa.Table, base_subquery.froms[0])
        pk_columns = list(table.primary_key.columns)
        if len(pk_columns) != 1:
            raise UnsupportedCompositePrimaryKeyError(
                f"Batch purger only supports single-column primary keys (table: {table.name})",
            )
        pk_col = pk_columns[0]
        entity_type = purger.spec.entity_type()

        await validate_conflict_checks(self._sess, purger.spec.conflict_checks())

        while True:
            sub = purger.spec.build_subquery().subquery()
            pk_subquery = sa.select(sub.c[pk_col.key]).limit(purger.batch_size)
            stmt = sa.delete(table).where(pk_col.in_(pk_subquery)).returning(pk_col)
            result = await self._sess.execute(stmt)
            deleted_pks = [row[0] for row in result.fetchall()]
            if not deleted_pks:
                break
            total_deleted += len(deleted_pks)
            cleanup = await self._delete_rbac_for_entities(
                entity_type, [str(pk) for pk in deleted_pks]
            )
            total_perm += cleanup.permission_count
            total_assoc += cleanup.scope_association_count
            if drop_virtual_scopes:
                await self._delete_virtual_scopes([
                    ScopeRef(scope_type=ScopeType(entity_type), scope_id=pk) for pk in deleted_pks
                ])
            if len(deleted_pks) < purger.batch_size:
                break

        return EntityBatchPurgerResult(
            deleted_count=total_deleted,
            deleted_permission_count=total_perm,
            deleted_scope_association_count=total_assoc,
        )

    # -- Virtual scope: member edges (entity_memberships + scope_bindings) --------

    async def _grant_auto_assign_roles(
        self,
        scope_id: ScopeId,
        user_ids: Collection[UserID],
    ) -> None:
        """Map users to every active ``auto_assign`` role bound to ``scope_id``.

        Roles bound to the scope are located via the scope-entity association
        (``association_scopes_entities`` with ``entity_type == ROLE``); already-granted
        pairs are skipped.
        """
        unique_user_ids = set(user_ids)
        if not unique_user_ids:
            return
        # One query: the scope's auto_assign roles, outer-joined with the target
        # users' existing grants (user_id is NULL for roles no target user holds).
        rows = (
            await self._sess.execute(
                sa.select(RoleRow.id.label("role_id"), UserRoleRow.user_id.label("user_id"))
                .join(
                    AssociationScopesEntitiesRow,
                    sa.cast(AssociationScopesEntitiesRow.entity_id, sa.String)
                    == sa.cast(RoleRow.id, sa.String),
                )
                .outerjoin(
                    UserRoleRow,
                    sa.and_(
                        UserRoleRow.role_id == RoleRow.id,
                        UserRoleRow.user_id.in_(unique_user_ids),
                    ),
                )
                .where(
                    AssociationScopesEntitiesRow.scope_type == scope_id.scope_type,
                    AssociationScopesEntitiesRow.scope_id == scope_id.scope_id,
                    AssociationScopesEntitiesRow.entity_type == LegacyEntityType.ROLE,
                    RoleRow.auto_assign.is_(True),
                    RoleRow.status == RoleStatus.ACTIVE,
                )
            )
        ).all()
        role_ids = {row.role_id for row in rows}
        existing_pairs = {(row.user_id, row.role_id) for row in rows if row.user_id is not None}
        specs = [
            UserRoleCreatorSpec(user_id=user_id, role_id=role_id)
            for user_id in unique_user_ids
            for role_id in role_ids
            if (user_id, role_id) not in existing_pairs
        ]
        if specs:
            await self.bulk_create(BulkCreator(specs=specs))

    async def create_full_user(
        self,
        full_creation: FullUserCreation,
    ) -> FullUserCreationResult:
        """Provision a user end to end in one transaction.

        Creates the user scope (row, virtual scope, own-scope roles) and grants those
        roles, creates the default keypair under the user scope and marks it as the
        user's main one, then enrolls the user in its domain's and projects'
        virtual scopes — the domain's model-store projects always included, and
        ``project_ids`` narrowed to projects that exist in the domain.
        """
        creation_result = await self.create_scope(full_creation.creation)
        user_row = creation_result.row
        user_id = UserID(user_row.uuid)
        # The user always holds its own scope's auto_assign roles (created just above).
        await self._grant_auto_assign_roles(
            ScopeId(scope_type=LegacyScopeType.USER, scope_id=str(user_id)),
            [user_id],
        )

        keypair_creator = KeyPairCreator(
            is_active=user_row.status == UserStatus.ACTIVE,
            is_admin=user_row.role in (UserRole.SUPERADMIN, UserRole.ADMIN),
            resource_policy=full_creation.keypair_resource_policy,
            rate_limit=full_creation.keypair_rate_limit,
        )
        kp_result = await self.create_scoped(
            RBACEntityCreator(
                spec=KeyPairCreatorSpec(
                    creator=keypair_creator,
                    generated_data=full_creation.keypair_secrets or generate_keypair_data(),
                    user_id=user_row.uuid,
                    email=user_row.email,
                    is_default=True,
                ),
                element_type=RBACElementType.KEYPAIR,
                scope_ref=RBACElementRef(RBACElementType.USER, str(user_row.uuid)),
            )
        )
        keypair_row = kp_result.row
        user_row.main_access_key = keypair_row.access_key

        member_scopes = [
            ScopeRef(scope_type=DOMAIN_SCOPE_TYPE, scope_id=full_creation.domain_id),
            *(
                ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=project_id)
                for project_id in await self._domain_member_project_ids(
                    full_creation.domain_id, full_creation.project_ids
                )
            ),
        ]
        await self._insert_virtual_scopes(member_scopes)
        await self.add_bulk_members([
            ScopeUserMember(target_scope=scope, user_id=user_id) for scope in member_scopes
        ])

        # Flushing the main_access_key update expires server-onupdate columns; reload
        # so callers can read the row without a sync-context lazy refresh.
        await self._sess.flush()
        await self._sess.refresh(user_row)
        return FullUserCreationResult(user_row=user_row, keypair_row=keypair_row)

    async def _domain_member_project_ids(
        self,
        domain_id: DomainID,
        project_ids: Collection[ProjectID],
    ) -> list[ProjectID]:
        """``project_ids`` narrowed to the domain's real projects, plus the domain's
        model-store projects that every user joins."""
        stmt = (
            sa.select(GroupRow.id)
            .join(DomainRow, DomainRow.name == GroupRow.domain_name)
            .where(
                DomainRow.id == domain_id,
                sa.or_(GroupRow.id.in_(project_ids), GroupRow.type == ProjectType.MODEL_STORE),
            )
        )
        return [ProjectID(row) for row in (await self._sess.scalars(stmt)).all()]

    async def add_bulk_members(
        self,
        memberships: Collection[ScopeMembership],
    ) -> None:
        """Attach each membership edge under its scope: membership in the scope's
        virtual scope, the legacy scope association, and the scope's binding into the
        member's own virtual scope — never the reverse binding, which would widen
        every member-scoped role at once. Grants each scope's auto_assign roles to
        members whose ``assign_role_on`` returns a user id.

        The edges may target any number of scopes; they are grouped and written per
        scope. Raises :class:`VirtualScopeNotFound` for any missing virtual scope.
        Idempotent: existing rows keep their ``permission_cap``.
        """
        edges_by_scope: dict[ScopeRef, list[ScopeMembership]] = defaultdict(list)
        for membership in memberships:
            edges_by_scope[membership.scope()].append(membership)
        if not edges_by_scope:
            return
        scope_vs_ids = await self._resolve_virtual_scope_ids(list(edges_by_scope.keys()))
        for scope, edges in edges_by_scope.items():
            await self._enroll_members_in_scope_vs(scope_vs_ids[scope], edges)
            await self._associate_entities_with_scope(scope, [e.entity_ref() for e in edges])
            await self._bind_scope_to_member_vs(scope, edges)
            await self._grant_member_auto_assign_roles(scope, edges)

    async def add_bulk_members_partial(
        self,
        memberships: Collection[ScopeMembership],
    ) -> EntityMembersResultWithFailures:
        """Add membership edges as :meth:`add_bulk_members` does, isolating each edge
        in its own savepoint: a failed edge — including one whose scope or member has
        no virtual scope — lands in ``errors`` while the rest are added. Roles are
        granted only for the successful edges.
        """
        successes: list[ScopeMembership] = []
        errors: list[EntityMemberCreationError] = []
        for index, membership in enumerate(memberships):
            # The handler stays outside the savepoint — see bulk_create_scoped_partial.
            try:
                async with self.savepoint():
                    scope = membership.scope()
                    virtual_scope_id = await self._resolve_virtual_scope_id(scope)
                    await self._enroll_members_in_scope_vs(virtual_scope_id, [membership])
                    await self._associate_entities_with_scope(scope, [membership.entity_ref()])
                    await self._bind_scope_to_member_vs(scope, [membership])
                successes.append(membership)
            except Exception as e:
                errors.append(
                    EntityMemberCreationError(membership=membership, exception=e, index=index)
                )
        successes_by_scope: dict[ScopeRef, list[ScopeMembership]] = defaultdict(list)
        for membership in successes:
            successes_by_scope[membership.scope()].append(membership)
        for scope, edges in successes_by_scope.items():
            await self._grant_member_auto_assign_roles(scope, edges)
        return EntityMembersResultWithFailures(successes=successes, errors=errors)

    async def _enroll_members_in_scope_vs(
        self,
        virtual_scope_id: VirtualScopeID,
        edges: Sequence[ScopeMembership],
    ) -> None:
        """Enroll each edge's entity in the scope's virtual scope with its cap."""
        await self._bulk_create_dependent_ignore_conflicts(
            [
                EntityMembershipCreatorSpec(
                    entity_ref=edge.entity_ref(), permission_cap=edge.permission_cap()
                )
                for edge in edges
            ],
            virtual_scope_id,
        )

    async def _associate_entities_with_scope(
        self,
        scope: ScopeRef,
        refs: Sequence[EntityRef],
    ) -> None:
        """Write each entity's legacy scope association."""
        await self._bulk_create_ignore_conflicts([
            self._association_spec(scope, ref) for ref in refs
        ])

    async def _bind_scope_to_member_vs(
        self,
        scope: ScopeRef,
        edges: Sequence[ScopeMembership],
    ) -> None:
        """Bind the scope into each edge's member virtual scope with the edge's cap;
        raises :class:`VirtualScopeNotFound` for members without one."""
        member_scopes = [self._member_scope_ref(edge.entity_ref()) for edge in edges]
        member_virtual_scope_ids = await self._resolve_virtual_scope_ids(member_scopes)
        await self._bulk_create_dependent_ignore_conflicts(
            [
                ScopeBindingCreatorSpec(
                    anchor_scope=member_scope,
                    bound_scope=scope,
                    permission_cap=edge.permission_cap(),
                )
                for edge, member_scope in zip(edges, member_scopes, strict=True)
            ],
            member_virtual_scope_ids,
        )

    @staticmethod
    def _member_scope_ref(ref: EntityRef) -> ScopeRef:
        """The member's own scope identity — every entity doubles as a scope."""
        return ScopeRef(scope_type=ScopeType(ref.entity_type), scope_id=ref.entity_id)

    @staticmethod
    def _association_spec(scope: ScopeRef, ref: EntityRef) -> AssociationScopesEntitiesCreatorSpec:
        return AssociationScopesEntitiesCreatorSpec(
            scope_id=ScopeId(
                scope_type=LegacyScopeType(scope.scope_type),
                scope_id=str(scope.scope_id),
            ),
            object_id=ObjectId(
                entity_type=LegacyEntityType(ref.entity_type),
                entity_id=str(ref.entity_id),
            ),
        )

    async def _grant_member_auto_assign_roles(
        self,
        scope: ScopeRef,
        members: Sequence[ScopeMembership],
    ) -> None:
        role_user_ids = [
            user_id for member in members if (user_id := member.assign_role_on()) is not None
        ]
        if role_user_ids:
            await self._grant_auto_assign_roles(
                ScopeId(
                    scope_type=LegacyScopeType(scope.scope_type),
                    scope_id=str(scope.scope_id),
                ),
                role_user_ids,
            )

    async def remove_bulk_members(
        self,
        scope: ScopeRef,
        entities: Collection[EntityRef],
    ) -> None:
        """Delete each member's membership, association, and the scope's binding in the
        member's own virtual scope; role mappings are left untouched. Missing virtual
        scopes (legacy data) never raise — whatever exists is deleted.
        """
        entity_refs = list(entities)
        if not entity_refs:
            return
        virtual_scope_id = await self._find_virtual_scope_id(scope)
        if virtual_scope_id is not None:
            await self._sess.execute(
                sa.delete(EntityMembershipRow).where(
                    EntityMembershipRow.virtual_scope_id == virtual_scope_id,
                    sa.tuple_(EntityMembershipRow.entity_type, EntityMembershipRow.entity_id).in_([
                        (ref.entity_type, ref.entity_id) for ref in entity_refs
                    ]),
                )
            )
        await self._sess.execute(
            sa.delete(AssociationScopesEntitiesRow).where(
                AssociationScopesEntitiesRow.scope_type == LegacyScopeType(scope.scope_type),
                AssociationScopesEntitiesRow.scope_id == str(scope.scope_id),
                sa.tuple_(
                    AssociationScopesEntitiesRow.entity_type,
                    AssociationScopesEntitiesRow.entity_id,
                ).in_([
                    (LegacyEntityType(ref.entity_type), str(ref.entity_id)) for ref in entity_refs
                ]),
            )
        )
        member_virtual_scope_ids = await self._find_virtual_scope_ids([
            self._member_scope_ref(ref) for ref in entity_refs
        ])
        if member_virtual_scope_ids:
            await self._sess.execute(
                sa.delete(ScopeBindingRow).where(
                    ScopeBindingRow.virtual_scope_id.in_(member_virtual_scope_ids.values()),
                    ScopeBindingRow.scope_type == scope.scope_type,
                    ScopeBindingRow.scope_id == scope.scope_id,
                )
            )

    # -- Virtual scope: ensure compatibility for externally-created rows ----------

    async def ensure_scope(self, scope: ScopeRef) -> None:
        """Ensure the virtual scope node for an already-created ``scope``. Idempotent."""
        await self._insert_virtual_scopes([scope])


class RBACOpsProvider(DBOpsProvider):
    """Hands out :class:`RBACWriteOps` for the read-write surface."""

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncIterator[RBACWriteOps]:
        async with self._db.begin_session_read_committed() as sess:
            yield RBACWriteOps(sess)

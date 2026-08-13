"""Entity writes of the v2 ops: every entity doubles as a scope.

Creating always provisions the row's virtual scope node with its self edges and
joins the scopes the spec's ``member_of`` declares; purging tears the same
things down. The role-managed variants — typed against the combined spec — also
provision the roles the scope type's active presets call for; the plain paths
never touch roles at all.
"""

from __future__ import annotations

import dataclasses
import logging
from collections import defaultdict
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

import jinja2
import jinja2.sandbox
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.common.data.entity.types import EntityRef, EntityType, ScopeRef, ScopeType
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.exception import RBACTypeConversionError
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.common.identifier.user import UserID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.permission.scope_template import ScopeTemplateValue
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import (
    OperationType,
    Permission,
    RoleSource,
)
from ai.backend.manager.data.permission.types import (
    ScopeType as LegacyScopeType,
)
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.manager.errors.role_preset import InvalidRoleNameTemplate
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.specs.creator import EntityCreator, RoleManagedEntityCreator
from ai.backend.manager.models.specs.membership import ScopeMembershipEntry
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import BulkResultWithFailures, IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter, RoleManagedEntityUpserter
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.ops.v2.write_base import V2WriteOpsBase

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass(frozen=True)
class _PresetRoleSpec:
    """One role a preset calls for on one scope, as plain values ready to write."""

    scope: ScopeRef
    name: str
    auto_assign: bool
    entity_operations: Mapping[RBACElementType, Sequence[OperationType]]


class V2EntityWriteOps(V2WriteOpsBase):
    """Writes of the entity family, bound to a single session."""

    # Rendered role names are stored in ``roles.name`` (sa.String(64)).
    _MAX_ROLE_NAME_LENGTH: ClassVar[int] = 64

    # Roles enroll in their scope's virtual scope as entities of this type.
    _ROLE_ENTITY_TYPE: ClassVar[EntityType] = EntityType("role")

    _template_env: jinja2.sandbox.ImmutableSandboxedEnvironment

    def __init__(self, sess: SASession) -> None:
        super().__init__(sess)
        self._template_env = jinja2.sandbox.ImmutableSandboxedEnvironment(
            undefined=jinja2.StrictUndefined,
        )

    async def create_entity[TRow: Base, TData](self, creator: EntityCreator[TRow, TData]) -> TData:
        """Insert one entity row: the row, its virtual scope node (self membership
        and self binding), and its membership in each ``member_of`` scope — one
        transaction. No roles are involved on this path."""
        row = creator.build_row()
        await self._insert_row(row, creator.integrity_error_checks())
        scope = creator.scope_of(row)
        await self._insert_scope_nodes([scope])
        await self._enroll_member(scope, creator.member_of(row))
        return creator.to_data(row)

    async def create_role_managed_entity[TRow: Base, TData](
        self, creator: RoleManagedEntityCreator[TRow, TData]
    ) -> TData:
        """Insert one role-managed entity row, additionally provisioning the roles
        the scope type's active presets call for — the spec's ``template_value``
        feeds the presets' name templates."""
        row = creator.build_row()
        await self._insert_row(row, creator.integrity_error_checks())
        scope = creator.scope_of(row)
        await self._insert_scope_nodes([scope])
        await self._create_preset_roles({scope: creator.template_value(row)})
        await self._enroll_member(scope, creator.member_of(row))
        return creator.to_data(row)

    async def bulk_create_entities[TRow: Base, TData](
        self, creators: Sequence[EntityCreator[TRow, TData]]
    ) -> list[TData]:
        """Insert entity rows atomically in one flush, provisioning each row's
        scope as :meth:`create_entity` does for one."""
        if not creators:
            return []
        rows = [creator.build_row() for creator in creators]
        await self._bulk_insert_rows(rows, creators[0].integrity_error_checks())
        scopes = [creator.scope_of(row) for creator, row in zip(creators, rows, strict=True)]
        await self._insert_scope_nodes(scopes)
        for creator, row, scope in zip(creators, rows, scopes, strict=True):
            await self._enroll_member(scope, creator.member_of(row))
        return [creator.to_data(row) for creator, row in zip(creators, rows, strict=True)]

    async def bulk_create_role_managed_entities[TRow: Base, TData](
        self, creators: Sequence[RoleManagedEntityCreator[TRow, TData]]
    ) -> list[TData]:
        """Insert role-managed entity rows atomically, provisioning each row's
        scope and preset roles as :meth:`create_role_managed_entity` does for one."""
        if not creators:
            return []
        rows = [creator.build_row() for creator in creators]
        await self._bulk_insert_rows(rows, creators[0].integrity_error_checks())
        scopes = [creator.scope_of(row) for creator, row in zip(creators, rows, strict=True)]
        await self._insert_scope_nodes(scopes)
        await self._create_preset_roles({
            scope: creator.template_value(row)
            for creator, row, scope in zip(creators, rows, scopes, strict=True)
        })
        for creator, row, scope in zip(creators, rows, scopes, strict=True):
            await self._enroll_member(scope, creator.member_of(row))
        return [creator.to_data(row) for creator, row in zip(creators, rows, strict=True)]

    async def purge_entity[TRow: Base, TData](
        self, purger: EntityPurger[TRow, TData]
    ) -> TData | None:
        """Delete one entity row and tear its scope down with it, symmetrically
        with the create: any permissions granted on the scope, its virtual scope
        node (FK cascade removes the edges inside it), and the edges the scope
        left in other virtual scopes; ``None`` if the row is already gone."""
        await self._validate_conflict_checks(purger.conflict_checks())
        row = await self._delete_row_returning(purger.row_class(), purger.pk_value())
        if row is None:
            return None
        await self._teardown_scope(purger.scope_of())
        return purger.to_data(row)

    async def bulk_purge_entities[TRow: Base, TData](
        self, purgers: Mapping[EntityID, EntityPurger[TRow, TData]]
    ) -> BulkResultWithFailures[TData]:
        """Delete each named entity independently; a row and its scope teardown
        share one savepoint, and a missing row is answered with
        :class:`EntityNotFoundError` rather than skipped."""
        successes: dict[EntityID, TData] = {}
        errors: dict[EntityID, Exception] = {}
        for entity_id, purger in purgers.items():
            try:
                async with self._sess.begin_nested():
                    data = await self.purge_entity(purger)
                    if data is None:
                        raise EntityNotFoundError(
                            f"{purger.row_class().__name__} {purger.pk_value()} not found"
                        )
                    successes[entity_id] = data
            except Exception as e:
                errors[entity_id] = e
        return BulkResultWithFailures(successes=successes, errors=errors)

    async def upsert_entity[TRow: Base, TData](
        self, upserter: EntityUpserter[TRow, TData]
    ) -> TData:
        """Insert or update an entity row on conflict; the scope stays provisioned
        idempotently — the virtual scope node is get-or-create, and the declared
        memberships are registered idempotently."""
        row = await self._upsert_row_returning(
            upserter.row_class(),
            upserter.index_elements(),
            upserter.build_insert_values(),
            upserter.build_update_values(),
            upserter.integrity_error_checks(),
        )
        scope = upserter.scope_of(row)
        await self._insert_scope_nodes([scope])
        await self._enroll_member(scope, upserter.member_of(row))
        return upserter.to_data(row)

    async def upsert_role_managed_entity[TRow: Base, TData](
        self, upserter: RoleManagedEntityUpserter[TRow, TData]
    ) -> TData:
        """Insert or update a role-managed entity row on conflict. Preset roles
        are provisioned only when the upsert actually created the scope, so an
        update never duplicates them."""
        row = await self._upsert_row_returning(
            upserter.row_class(),
            upserter.index_elements(),
            upserter.build_insert_values(),
            upserter.build_update_values(),
            upserter.integrity_error_checks(),
        )
        scope = upserter.scope_of(row)
        created = await self._insert_scope_nodes([scope])
        if scope in created:
            await self._create_preset_roles({scope: upserter.template_value(row)})
        await self._enroll_member(scope, upserter.member_of(row))
        return upserter.to_data(row)

    # -- Scope provisioning -------------------------------------------------------

    async def _bulk_insert_rows[TRow: Base](
        self, rows: Sequence[TRow], checks: Sequence[IntegrityErrorCheck]
    ) -> None:
        """Flush pre-built rows in one batch. Takes plain values so both entity
        creator families share it without a common spec supertype."""
        self._sess.add_all(rows)
        try:
            await self._sess.flush()
        except sa.exc.IntegrityError as e:
            self._match_integrity_error(self._parse_integrity_error(e), checks)

    async def _insert_scope_nodes(self, scopes: Sequence[ScopeRef]) -> set[ScopeRef]:
        """Create each scope's virtual scope node with its self entity-membership and
        self scope-binding (permission_cap NULL). Idempotent: an existing node is a
        no-op. Returns the scopes whose node was actually created."""
        if not scopes:
            return set()
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
            return set()
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
        return {
            ScopeRef(scope_type=ScopeType(EntityType(row.scope_type)), scope_id=row.scope_id)
            for row in inserted
        }

    async def _enroll_member(self, member: ScopeRef, parent_scopes: Collection[ScopeRef]) -> None:
        """Enroll the new entity as a member of each parent scope: membership in
        the parent's virtual scope, and the parent's binding into the member's own
        virtual scope — permission_cap NULL throughout, since capped sharing is the
        object-sharing mechanism, not creation.

        Pure graph edges — no role state is touched here; granting a joining
        user the parents' auto_assign roles is the explicit
        :meth:`_grant_auto_assign_roles` primitive, wired by the user domain. A
        parent without a virtual scope raises :class:`VirtualScopeNotFound`.
        """
        if not parent_scopes:
            return
        member_ref = EntityRef(entity_type=member.scope_type, entity_id=member.scope_id)
        await self._record_memberships([
            ScopeMembershipEntry(member=member_ref, parent_scope=parent) for parent in parent_scopes
        ])
        member_virtual_scope_id = (await self._resolve_virtual_scope_ids([member]))[member]
        await self._bulk_insert_ignore_conflicts(
            [
                ScopeBindingRow(
                    virtual_scope_id=member_virtual_scope_id,
                    scope_type=parent.scope_type,
                    scope_id=parent.scope_id,
                    permission_cap=None,
                )
                for parent in parent_scopes
            ],
        )

    async def _grant_auto_assign_roles(self, scopes: Collection[ScopeRef], user_id: UserID) -> None:
        """Map the user to every active auto_assign role enrolled in ``scopes``'
        virtual scopes; already-granted pairs are skipped via the (user_id, role_id)
        unique key.

        Not called by the generic entity paths: whether (and for which scopes — the
        joined ones, the user's own) a creation grants roles is the user domain's
        decision, wired explicitly during its migration."""
        role_ids = (
            await self._sess.scalars(
                sa.select(RoleRow.id)
                .join(EntityMembershipRow, EntityMembershipRow.entity_id == RoleRow.id)
                .join(
                    VirtualScopeRow,
                    EntityMembershipRow.virtual_scope_id == VirtualScopeRow.id,
                )
                .where(
                    sa.tuple_(VirtualScopeRow.scope_type, VirtualScopeRow.scope_id).in_([
                        (s.scope_type, s.scope_id) for s in scopes
                    ]),
                    EntityMembershipRow.entity_type == self._ROLE_ENTITY_TYPE,
                    RoleRow.auto_assign.is_(True),
                    RoleRow.status == RoleStatus.ACTIVE,
                )
            )
        ).all()
        if role_ids:
            await self._bulk_insert_ignore_conflicts(
                [UserRoleRow(user_id=user_id, role_id=role_id) for role_id in role_ids],
            )

    async def _teardown_scope(self, scope: ScopeRef) -> None:
        """Remove everything the scope's provisioning and lifetime accumulated: any
        permissions granted on it, its virtual scope node (FK cascade removes the
        edges inside it, the enrolled roles' memberships included), and the edges
        the scope left in other virtual scopes."""
        permission_scope_type = self._permission_scope_type(scope.scope_type)
        if permission_scope_type is not None:
            # Types outside the RBAC element enum can never have carried permissions.
            await self._sess.execute(
                sa.delete(PermissionRow).where(
                    PermissionRow.scope_type == permission_scope_type,
                    PermissionRow.scope_id == str(scope.scope_id),
                )
            )
        await self._sess.execute(
            sa.delete(VirtualScopeRow).where(
                VirtualScopeRow.scope_type == scope.scope_type,
                VirtualScopeRow.scope_id == scope.scope_id,
            )
        )
        await self._sess.execute(
            sa.delete(ScopeBindingRow).where(
                ScopeBindingRow.scope_type == scope.scope_type,
                ScopeBindingRow.scope_id == scope.scope_id,
            )
        )
        await self._sess.execute(
            sa.delete(EntityMembershipRow).where(
                EntityMembershipRow.entity_type == scope.scope_type,
                EntityMembershipRow.entity_id == scope.scope_id,
            )
        )

    def _permission_scope_type(self, scope_type: ScopeType) -> LegacyScopeType | None:
        """The ``permissions.scope_type`` value for ``scope_type``, or ``None`` for
        types outside the RBAC element enum (which can carry no permissions)."""
        try:
            return RBACElementType(scope_type).to_scope_type()
        except ValueError:
            return None

    # -- Preset-derived roles (role-managed paths only) ---------------------------

    def _scope_element_type(self, scope_type: ScopeType) -> RBACElementType:
        try:
            return RBACElementType(scope_type)
        except ValueError as e:
            raise RBACTypeConversionError(
                f"Scope type {scope_type!r} has no corresponding RBAC element type"
            ) from e

    async def _create_preset_roles(
        self, scope_values: Mapping[ScopeRef, ScopeTemplateValue]
    ) -> None:
        """Create the roles the active presets matching the scopes' types call for —
        presets are the only source of a scope's roles. Each role is enrolled in
        its scope's virtual scope (the scope owns its roles)."""
        specs = await self._preset_role_specs(scope_values)
        if not specs:
            return
        role_rows = [
            RoleRow(
                name=spec.name,
                source=RoleSource.SYSTEM,
                status=RoleStatus.ACTIVE,
                auto_assign=spec.auto_assign,
            )
            for spec in specs
        ]
        self._sess.add_all(role_rows)
        await self._sess.flush()
        await self._record_memberships([
            ScopeMembershipEntry(
                member=EntityRef(entity_type=self._ROLE_ENTITY_TYPE, entity_id=row.id),
                parent_scope=spec.scope,
            )
            for spec, row in zip(specs, role_rows, strict=True)
        ])
        permission_rows = [
            PermissionRow(
                role_id=row.id,
                scope_type=self._scope_element_type(spec.scope.scope_type).to_scope_type(),
                scope_id=str(spec.scope.scope_id),
                entity_type=entity_type.to_entity_type(),
                operation=operation,
                permission=Permission.from_operation(operation),
            )
            for spec, row in zip(specs, role_rows, strict=True)
            for entity_type, operations in spec.entity_operations.items()
            for operation in operations
        ]
        if permission_rows:
            self._sess.add_all(permission_rows)
            await self._sess.flush()

    async def _preset_role_specs(
        self, scope_values: Mapping[ScopeRef, ScopeTemplateValue]
    ) -> list[_PresetRoleSpec]:
        """The roles the active presets matching the scopes' types call for."""
        scopes = list(scope_values)
        if not scopes:
            return []
        preset_rows = (
            await self._sess.scalars(
                sa.select(RolePresetRow).where(
                    RolePresetRow.scope_type.in_({
                        self._scope_element_type(scope.scope_type).to_scope_type()
                        for scope in scopes
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
        return [
            _PresetRoleSpec(
                scope=scope,
                name=self._preset_role_name(preset, scope, scope_values[scope]),
                auto_assign=preset.auto_assign,
                entity_operations={
                    entity_type: tuple(operations)
                    for entity_type, operations in operations_by_preset[preset.id].items()
                },
            )
            for scope in scopes
            for preset in presets_by_scope_type[
                self._scope_element_type(scope.scope_type).to_scope_type()
            ]
        ]

    def _preset_role_name(
        self, preset: RolePresetRow, scope: ScopeRef, template_value: ScopeTemplateValue
    ) -> str:
        """The name of a role instantiated from the preset: a preset without a
        template gets a generated per-scope name; a template that cannot be rendered
        falls back to a deterministic name, so entity creation never fails on role
        naming. The template sees the spec-declared values — no lookup."""
        if preset.role_name_template is None:
            return self._default_preset_role_name(preset, scope)
        try:
            return self._render_role_name(preset.role_name_template, template_value)
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

    def _default_preset_role_name(self, preset: RolePresetRow, scope: ScopeRef) -> str:
        """Generated per-scope name for a preset that declares no template: the
        preset name suffixed with the scope id, so roles of different scopes (and of
        different presets on one scope) stay distinguishable."""
        suffix = f"-{str(scope.scope_id)[:8]}"
        return f"{preset.name[: self._MAX_ROLE_NAME_LENGTH - len(suffix)]}{suffix}"

    def _fallback_preset_role_name(self, scope: ScopeRef) -> str:
        """Deterministic per-scope role name used when a preset's template cannot be
        rendered. Built with plain string formatting — never via the template engine —
        so entity creation cannot fail on role naming."""
        return f"{scope.scope_type}-{str(scope.scope_id)[:8]}-role"

    def _render_role_name(self, template: str, scope: ScopeTemplateValue) -> str:
        """Render a role name from a preset's ``role_name_template``, raising
        :class:`InvalidRoleNameTemplate` on syntax errors, undefined variables, or
        an empty result.

        An over-long render is truncated to the column limit rather than treated
        as a failure — the template produced a usable name, and discarding it for
        the generic fallback would lose the declared intent (the template-less
        default name truncates the same way)."""
        try:
            rendered = self._template_env.from_string(template).render(
                scope=dataclasses.asdict(scope),
            )
        except jinja2.TemplateError as e:
            raise InvalidRoleNameTemplate(f"Failed to render role name template: {e}") from e
        rendered = rendered.strip()
        if not rendered:
            raise InvalidRoleNameTemplate("Role name template rendered to an empty string.")
        return rendered[: self._MAX_ROLE_NAME_LENGTH]

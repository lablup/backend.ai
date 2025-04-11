import logging
from decimal import Decimal
from typing import Callable, Optional, cast

import sqlalchemy as sa
import trafaret as t
from graphene import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import (
    DefaultForUnspecified,
    ResourceSlot,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.api.exceptions import ObjectNotFound
from ai.backend.manager.config import SharedConfig
from ai.backend.manager.models.agent import AgentStatus, agents
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.group import association_groups_users, groups
from ai.backend.manager.models.kernel import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    KernelRow,
)
from ai.backend.manager.models.resource_preset import QueryStatement, ResourcePresetRow
from ai.backend.manager.models.scaling_group import query_allowed_sgroups
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, execute_with_txn_retry
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.services.resource_preset.actions.check_presets import (
    CheckResourcePresetsAction,
    CheckResourcePresetsActionResult,
)
from ai.backend.manager.services.resource_preset.actions.create_preset import (
    CreateResourcePresetAction,
    CreateResourcePresetActionResult,
)
from ai.backend.manager.services.resource_preset.actions.delete_preset import (
    DeleteResourcePresetAction,
    DeleteResourcePresetActionResult,
)
from ai.backend.manager.services.resource_preset.actions.list_presets import (
    ListResourcePresetsAction,
    ListResourcePresetsResult,
)
from ai.backend.manager.services.resource_preset.actions.modify_preset import (
    ModifyResourcePresetAction,
    ModifyResourcePresetActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def filter_by_name(name: str) -> Callable[[QueryStatement], QueryStatement]:
    return lambda query_stmt: query_stmt.where(ResourcePresetRow.name == name)


def filter_by_id(id: UUID) -> Callable[[QueryStatement], QueryStatement]:
    return lambda query_stmt: query_stmt.where(ResourcePresetRow.id == id)


class ResourcePresetService:
    _db: ExtendedAsyncSAEngine
    _shared_config: SharedConfig
    _agent_registry: AgentRegistry

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        agent_registry: AgentRegistry,
        shared_config: SharedConfig,
    ) -> None:
        self._db = db
        self._agent_registry = agent_registry
        self._shared_config = shared_config

    async def create_preset(
        self, action: CreateResourcePresetAction
    ) -> CreateResourcePresetActionResult:
        name = action.creator.name
        creator = action.creator

        async def _create(db_session: AsyncSession) -> Optional[ResourcePresetRow]:
            return await ResourcePresetRow.create(creator, db_session=db_session)

        async with self._db.connect() as db_conn:
            preset_row = await execute_with_txn_retry(_create, self._db.begin_session, db_conn)
        if preset_row is None:
            raise ValueError(
                f"Duplicate resource preset name (name:{name}, scaling_group:{creator.scaling_group_name})"
            )

        return CreateResourcePresetActionResult(resource_preset=preset_row)

    async def modify_preset(
        self, action: ModifyResourcePresetAction
    ) -> ModifyResourcePresetActionResult:
        name = action.name
        preset_id = action.id
        modifier = action.modifier

        if preset_id is None and name is None:
            raise ValueError("One of (`id` or `name`) parameter should be not null")

        async with self._db.begin_session() as db_sess:
            if preset_id is not None:
                preset_row = (
                    await db_sess.execute(
                        sa.select(
                            ResourcePresetRow,
                        ).where(ResourcePresetRow.id == preset_id)
                    )
                ).scalar_one_or_none()
            else:
                preset_row = (
                    await db_sess.execute(
                        sa.select(
                            ResourcePresetRow,
                        ).where(ResourcePresetRow.name == name)
                    )
                ).scalar_one_or_none()

            if preset_row is None:
                raise ObjectNotFound("Resource preset not found")
            to_update = modifier.fields_to_update()
            for key, value in to_update.items():
                setattr(preset_row, key, value)
            await db_sess.flush()

        return ModifyResourcePresetActionResult(resource_preset=preset_row)

    async def delete_preset(
        self, action: DeleteResourcePresetAction
    ) -> DeleteResourcePresetActionResult:
        name = action.name
        preset_id = action.id

        if preset_id is None and name is None:
            raise ValueError("One of (`id` or `name`) parameter should be not null")

        async with self._db.begin_session() as db_sess:
            if preset_id is not None:
                preset_row = (
                    await db_sess.execute(
                        sa.select(
                            ResourcePresetRow,
                        ).where(ResourcePresetRow.id == preset_id)
                    )
                ).scalar_one_or_none()
            else:
                preset_row = (
                    await db_sess.execute(
                        sa.select(
                            ResourcePresetRow,
                        ).where(ResourcePresetRow.name == name)
                    )
                ).scalar_one_or_none()

            if preset_row is None:
                raise ObjectNotFound("Resource preset not found")

            await db_sess.delete(preset_row)

        return DeleteResourcePresetActionResult(resource_preset=preset_row)

    async def list_presets(self, action: ListResourcePresetsAction) -> ListResourcePresetsResult:
        # TODO: Remove this?
        await self._shared_config.get_resource_slots()

        async with self._db.begin_readonly_session() as db_session:
            query = sa.select(ResourcePresetRow)
            query_condition = ResourcePresetRow.scaling_group_name.is_(sa.null())
            scaling_group_name = action.scaling_group
            if scaling_group_name is not None:
                query_condition = sa.or_(
                    query_condition, ResourcePresetRow.scaling_group_name == scaling_group_name
                )
            query = query.where(query_condition)
            presets = []
            async for row in await db_session.stream_scalars(query):
                row = cast(ResourcePresetRow, row)
                preset_slots = row.resource_slots.normalize_slots(ignore_unknown=True)
                presets.append({
                    "id": str(row.id),
                    "name": row.name,
                    "shared_memory": str(row.shared_memory) if row.shared_memory else None,
                    "resource_slots": preset_slots.to_json(),
                })

            return ListResourcePresetsResult(presets=presets)

    async def check_presets(
        self, action: CheckResourcePresetsAction
    ) -> CheckResourcePresetsActionResult:
        access_key = action.access_key
        resource_policy = action.resource_policy
        domain_name = action.domain_name

        known_slot_types = await self._shared_config.get_resource_slots()

        async with self._db.begin_readonly() as conn:
            # Check keypair resource limit.
            keypair_limits = ResourceSlot.from_policy(resource_policy, known_slot_types)
            keypair_occupied = await self._agent_registry.get_keypair_occupancy(
                access_key, db_sess=SASession(conn)
            )
            keypair_remaining = keypair_limits - keypair_occupied

            # Check group resource limit and get group_id.
            j = sa.join(
                groups,
                association_groups_users,
                association_groups_users.c.group_id == groups.c.id,
            )
            query = (
                sa.select([groups.c.id, groups.c.total_resource_slots])
                .select_from(j)
                .where(
                    (association_groups_users.c.user_id == action.user_id)
                    & (groups.c.name == action.group)
                    & (groups.c.domain_name == domain_name),
                )
            )
            result = await conn.execute(query)
            row = result.first()
            if row is None:
                raise InvalidAPIParameters(f"Unknown project (name: {action.group})")
            group_id = row["id"]
            group_resource_slots = row["total_resource_slots"]
            if group_id is None:
                raise InvalidAPIParameters(f"Unknown project (name: {action.group})")
            group_resource_policy = {
                "total_resource_slots": group_resource_slots,
                "default_for_unspecified": DefaultForUnspecified.UNLIMITED,
            }
            group_limits = ResourceSlot.from_policy(group_resource_policy, known_slot_types)
            group_occupied = await self._agent_registry.get_group_occupancy(
                group_id, db_sess=SASession(conn)
            )
            group_remaining = group_limits - group_occupied

            # Check domain resource limit.
            query = sa.select([domains.c.total_resource_slots]).where(domains.c.name == domain_name)
            domain_resource_slots = await conn.scalar(query)
            domain_resource_policy = {
                "total_resource_slots": domain_resource_slots,
                "default_for_unspecified": DefaultForUnspecified.UNLIMITED,
            }
            domain_limits = ResourceSlot.from_policy(domain_resource_policy, known_slot_types)
            domain_occupied = await self._agent_registry.get_domain_occupancy(
                domain_name, db_sess=SASession(conn)
            )
            domain_remaining = domain_limits - domain_occupied

            # Take minimum remaining resources. There's no need to merge limits and occupied.
            # To keep legacy, we just merge all remaining slots into `keypair_remainig`.
            for slot in known_slot_types:
                keypair_remaining[slot] = min(
                    keypair_remaining[slot],
                    group_remaining[slot],
                    domain_remaining[slot],
                )

            # Prepare per scaling group resource.
            sgroups = await query_allowed_sgroups(conn, domain_name, group_id, access_key)
            sgroup_names = [sg.name for sg in sgroups]
            if action.scaling_group is not None:
                if action.scaling_group not in sgroup_names:
                    raise InvalidAPIParameters("Unknown scaling group")
                sgroup_names = [action.scaling_group]
            per_sgroup = {
                sgname: {
                    "using": ResourceSlot({k: Decimal(0) for k in known_slot_types.keys()}),
                    "remaining": ResourceSlot({k: Decimal(0) for k in known_slot_types.keys()}),
                }
                for sgname in sgroup_names
            }

            # Per scaling group resource using from resource occupying kernels.
            j = sa.join(KernelRow, SessionRow, KernelRow.session_id == SessionRow.id)
            query = (
                sa.select([KernelRow.occupied_slots, SessionRow.scaling_group_name])
                .select_from(j)
                .where(
                    (KernelRow.user_uuid == action.user_id)
                    & (KernelRow.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                    & (SessionRow.scaling_group_name.in_(sgroup_names)),
                )
            )
            async for row in await conn.stream(query):
                per_sgroup[row["scaling_group_name"]]["using"] += row["occupied_slots"]

            # Per scaling group resource remaining from agents stats.
            sgroup_remaining = ResourceSlot({k: Decimal(0) for k in known_slot_types.keys()})
            query = (
                sa.select([
                    agents.c.available_slots,
                    agents.c.occupied_slots,
                    agents.c.scaling_group,
                ])
                .select_from(agents)
                .where(
                    (agents.c.status == AgentStatus.ALIVE)
                    & (agents.c.scaling_group.in_(sgroup_names)),
                )
            )
            agent_slots = []
            async for row in await conn.stream(query):
                remaining = row["available_slots"] - row["occupied_slots"]
                remaining += ResourceSlot({k: Decimal(0) for k in known_slot_types.keys()})
                sgroup_remaining += remaining
                agent_slots.append(remaining)
                per_sgroup[row["scaling_group"]]["remaining"] += remaining

            # Take maximum allocatable resources per sgroup.
            for sgname, sgfields in per_sgroup.items():
                for rtype, slots in sgfields.items():
                    if rtype == "remaining":
                        for slot in known_slot_types.keys():
                            if slot in slots:
                                slots[slot] = min(keypair_remaining[slot], slots[slot])
                    per_sgroup[sgname][rtype] = slots.to_json()  # type: ignore  # it's serialization
            for slot in known_slot_types.keys():
                sgroup_remaining[slot] = min(keypair_remaining[slot], sgroup_remaining[slot])

            # Fetch all resource presets in the current scaling group.
            resource_preset_query = sa.select(ResourcePresetRow)
            query_condition = ResourcePresetRow.scaling_group_name.is_(sa.null())
            if action.scaling_group is not None:
                query_condition = sa.or_(
                    query_condition,
                    ResourcePresetRow.scaling_group_name == action.scaling_group,
                )
            resource_preset_query = resource_preset_query.where(query_condition)

            presets = []
            async for row in await SASession(conn).stream_scalars(resource_preset_query):
                # Check if there are any agent that can allocate each preset.
                row = cast(ResourcePresetRow, row)
                allocatable = False
                preset_slots = row.resource_slots.normalize_slots(ignore_unknown=True)
                for agent_slot in agent_slots:
                    if agent_slot >= preset_slots and keypair_remaining >= preset_slots:
                        allocatable = True
                        break
                presets.append({
                    "id": str(row.id),
                    "name": row.name,
                    "resource_slots": preset_slots.to_json(),
                    "shared_memory": (
                        str(row.shared_memory) if row.shared_memory is not None else None
                    ),
                    "allocatable": allocatable,
                })

            # Return group resource status as NaN if not allowed.
            group_resource_visibility = await self._shared_config.get_raw(
                "config/api/resources/group_resource_visibility"
            )
            group_resource_visibility = t.ToBool().check(group_resource_visibility)
            if not group_resource_visibility:
                group_limits = ResourceSlot({k: Decimal("NaN") for k in known_slot_types.keys()})
                group_occupied = ResourceSlot({k: Decimal("NaN") for k in known_slot_types.keys()})
                group_remaining = ResourceSlot({k: Decimal("NaN") for k in known_slot_types.keys()})

            return CheckResourcePresetsActionResult(
                presets=presets,
                keypair_limits=keypair_limits.to_json(),
                keypair_using=keypair_occupied.to_json(),
                keypair_remaining=keypair_remaining.to_json(),
                group_limits=group_limits.to_json(),
                group_using=group_occupied.to_json(),
                group_remaining=group_remaining.to_json(),
                scaling_group_remaining=sgroup_remaining.to_json(),
                scaling_groups=per_sgroup,
            )
